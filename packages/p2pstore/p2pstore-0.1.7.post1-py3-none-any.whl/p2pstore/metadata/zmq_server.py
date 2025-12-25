"""
ZMQ Metadata Server 实现.

这是一个轻量级的元数据服务器，只负责：
1. 接收和广播元数据消息 (PUB/SUB)
2. 处理查询请求 (ROUTER/DEALER)

与 P2PClient 完全解耦，不涉及数据传输。
"""

import json
import time
from threading import Lock, Thread

import zmq

from ..core import MetadataServer
from ..utils.logger import LoggerManager


class ZMQMetadataServer(MetadataServer):
    """
    ZMQ 元数据服务器.

    只负责元数据的广播和查询，不涉及数据传输。
    使用 PUB socket 广播消息，ROUTER socket 处理查询请求。
    """

    def __init__(self, sync_addr: str, coord_addr: str):
        """
        初始化 ZMQ Metadata Server.

        Args:
            sync_addr: ZMQ PUB 绑定地址 (tcp://0.0.0.0:5765)
            coord_addr: ZMQ ROUTER 绑定地址 (tcp://0.0.0.0:5766)
        """
        self.sync_addr = sync_addr
        self.coord_addr = coord_addr
        self.logger = LoggerManager.get_logger("zmq-metadata-server")

        self.context = zmq.Context.instance()
        self.providers: dict[str, dict] = {}
        # file_map: {file_key: {"host": ..., "metadata": {...}}}
        self.file_map: dict[str, dict] = {}
        self.lock = Lock()

        self._init_sockets()
        self.running = True
        self._start_threads()

        self.logger.info("ZMQ Metaserver 已启动")
        self.logger.info("  PUB  地址: %s", sync_addr)
        self.logger.info("  ROUTER 地址: %s", coord_addr)

    def _init_sockets(self) -> None:
        """初始化 ZMQ sockets."""
        # PUB socket 用于广播消息
        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_socket.bind(self.sync_addr)
        self.logger.info("PUB 绑定: %s", self.sync_addr)

        # ROUTER socket 用于处理请求
        self.router_socket = self.context.socket(zmq.ROUTER)
        self.router_socket.bind(self.coord_addr)
        self.logger.info("ROUTER 绑定: %s", self.coord_addr)

    def _start_threads(self) -> None:
        """启动查询处理线程."""
        self.query_thread = Thread(target=self._query_handler, daemon=True)
        self.query_thread.start()

    def _query_handler(self) -> None:
        """处理来自 Client 的请求."""
        self.logger.info("查询处理线程启动")
        while self.running:
            try:
                frames = self.router_socket.recv_multipart()
                if not frames:
                    continue

                identity = frames[0]
                msg_data = b""
                if len(frames) >= 3:
                    msg_data = frames[2]
                elif len(frames) == 2 and frames[1] != b"":
                    msg_data = frames[1]
                elif len(frames) == 1:
                    self.logger.warning("收到无消息帧, 跳过")
                    continue

                if not msg_data:
                    response = {"code": 2, "msg": "空请求"}
                else:
                    try:
                        msg = json.loads(msg_data.decode("utf-8"))
                        response = self._process_request(msg)
                    except UnicodeDecodeError:
                        response = {"code": 3, "msg": "编码错误"}
                    except json.JSONDecodeError:
                        response = {"code": 4, "msg": "JSON格式错误"}

                self.router_socket.send_multipart(
                    [identity, b"", json.dumps(response).encode("utf-8")]
                )
            except zmq.ZMQError as exc:
                if self.running:
                    self.logger.error("ROUTER 异常: %s", exc, exc_info=True)
            except Exception as exc:
                self.logger.error("查询处理异常: %s", exc, exc_info=True)

    def _process_request(self, msg: dict) -> dict:
        """处理请求消息."""
        msg_type = msg.get("type")
        self.logger.debug("处理请求: type=%s", msg_type)

        if msg_type == "query_file":
            return self._handle_query_file(msg)
        elif msg_type == "list_files":
            return self._handle_list_files()
        elif msg_type == "publish":
            return self._handle_publish(msg)
        elif msg_type == "delete_file":
            return self._handle_delete_file(msg)
        elif msg_type == "clear_files":
            return self._handle_clear_files()
        else:
            return {"code": 2, "msg": f"不支持的请求类型: {msg_type}"}

    def _handle_query_file(self, msg: dict) -> dict:
        """处理文件查询请求。"""
        key = msg.get("key")
        with self.lock:
            if key in self.file_map:
                entry = self.file_map[key]
                return {
                    "code": 0,
                    "data": {
                        "host": entry["host"],
                        "metadata": entry["metadata"],
                    },
                }
            return {"code": 1, "msg": f"数据 {key} 不存在"}

    def _handle_list_files(self) -> dict:
        """处理列出所有文件请求."""
        with self.lock:
            return {"code": 0, "data": dict(self.file_map)}

    def _handle_publish(self, msg: dict) -> dict:
        """处理广播请求：转发给所有订阅者."""
        payload = msg.get("payload", {})
        if payload:
            self.pub_socket.send_json(payload)
            self._process_broadcast(payload)  # 本地也处理
            self.logger.debug("广播消息: type=%s", payload.get("type"))
        return {"code": 0, "msg": "published"}

    def _handle_delete_file(self, msg: dict) -> dict:
        """处理删除文件请求。"""
        file_key = msg.get("key")

        with self.lock:
            if file_key not in self.file_map:
                return {"code": 1, "success": False, "msg": f"文件 {file_key} 不存在"}
            # 获取旧数据的 host，用于通知释放内存
            old_host = self.file_map[file_key].get("host")

        try:
            unregister_msg = {
                "type": "file_unregister",
                "file_key": file_key,
                "host": old_host,  # 通知原 host 释放内存
                "timestamp": time.time(),
            }
            self.pub_socket.send_json(unregister_msg)
            self._process_broadcast(unregister_msg)
            return {"code": 0, "success": True}
        except Exception as e:
            self.logger.error("删除文件 %s 失败: %s", file_key, e)
            return {"code": 2, "success": False, "msg": str(e)}

    def _handle_clear_files(self) -> dict:
        """处理清空所有文件请求."""
        with self.lock:
            keys_to_clear = list(self.file_map.keys())

        cleared = []
        failed = []
        for key in keys_to_clear:
            try:
                unregister_msg = {
                    "type": "file_unregister",
                    "file_key": key,
                    "timestamp": time.time(),
                }
                self.pub_socket.send_json(unregister_msg)
                self._process_broadcast(unregister_msg)
                cleared.append(key)
            except Exception as e:
                self.logger.error("清除文件 %s 失败: %s", key, e)
                failed.append(key)

        return {
            "code": 0,
            "success": len(failed) == 0,
            "cleared": len(cleared),
            "failed": failed,
        }

    def delete_prefix(self, prefix: str) -> bool:
        """根据前缀删除文件 (暂未实现)."""
        pass

    def delete_prefix_batch(self, prefixes: list[str]) -> dict[str, bool]:
        """批量根据前缀删除文件 (暂未实现)."""
        pass

    def _process_broadcast(self, msg: dict) -> None:
        """处理广播消息，更新本地状态."""
        with self.lock:
            msg_type = msg.get("type")

            if msg_type == "register":
                host = msg.get("host")
                if host:
                    self.providers[host] = {
                        "heartbeat": msg.get("timestamp"),
                        "load": 0,
                    }
                    self.logger.info("Provider 注册: %s", host)

            elif msg_type == "unregister":
                host = msg.get("host")
                if host and host in self.providers:
                    del self.providers[host]
                    self.logger.info("Provider 注销: %s", host)

            elif msg_type == "heartbeat":
                host = msg.get("host")
                if host and host in self.providers:
                    self.providers[host]["heartbeat"] = msg.get("timestamp")

            elif msg_type == "file_register":
                file_key = msg.get("file_key", "")
                host = msg.get("host")
                if file_key and host:
                    metadata = {
                        "object_type": msg.get("object_type", ""),
                        "data_size": msg.get("data_size", msg.get("file_size", 0)),
                        "tensor_shape": msg.get("tensor_shape", ()),
                        "tensor_dtype": msg.get("tensor_dtype"),
                        "buffer_ptr": msg.get("buffer_ptr"),
                    }
                    # 直接覆盖，单副本模式
                    self.file_map[file_key] = {"host": host, "metadata": metadata}
                    self.logger.info("文件注册: %s -> %s", file_key, host)

            elif msg_type == "file_unregister":
                file_key = msg.get("file_key")
                if file_key and file_key in self.file_map:
                    del self.file_map[file_key]
                    self.logger.info("文件注销: %s", file_key)

            elif msg_type == "load_update":
                host = msg.get("host")
                if host and host in self.providers:
                    self.providers[host]["load"] = max(
                        0, self.providers[host]["load"] + msg.get("delta", 0)
                    )

    def get_stats(self) -> dict:
        """获取当前状态统计."""
        with self.lock:
            return {
                "providers": len(self.providers),
                "files": len(self.file_map),
                "provider_list": list(self.providers.keys()),
                "file_list": list(self.file_map.keys()),
            }

    def close(self) -> None:
        """关闭 Metaserver."""
        self.logger.info("正在关闭 ZMQ Metaserver...")
        self.running = False
        time.sleep(0.3)

        # 关闭 sockets
        try:
            self.pub_socket.close(linger=0)
            self.router_socket.close(linger=0)
        except Exception as e:
            self.logger.error("关闭 socket 异常: %s", e)

        self.logger.info("ZMQ Metaserver 已关闭")
