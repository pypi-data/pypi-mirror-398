"""
ZMQ Metadata Client 实现模块.

该模块实现了基于 ZeroMQ 的元数据客户端 `ZMQMetadataClient`。
- 使用 SUB socket 订阅来自 Metaserver 的广播消息
- 使用 DEALER socket 向 Metaserver 发送请求

注意: Metaserver 由独立的 ZMQMetadataServer 类实现 (见 zmq_server.py)
"""

import json
import time
from threading import Lock, Thread

import zmq

from ..core import MetadataClient
from ..utils.logger import LoggerManager


class ZMQMetadataClient(MetadataClient):
    """
    ZMQ 元数据客户端.

    连接到独立的 ZMQMetaserver，通过 SUB 接收广播，通过 DEALER 发送请求。
    """

    def __init__(self, sync_addr: str, coord_addr: str, local_ip: str):
        """
        初始化 ZMQ Metadata Store 客户端.

        Args:
            sync_addr: ZMQ SUB 连接地址 (tcp://{METASERVER_IP}:5765)
            coord_addr: ZMQ DEALER 连接地址 (tcp://{METASERVER_IP}:5766)
            local_ip: 本地 IP 地址
        """
        self.sync_addr = sync_addr
        self.coord_addr = coord_addr
        self.local_ip = local_ip
        self.logger = LoggerManager.get_logger("zmq-metadata-client")

        self.context = zmq.Context.instance()
        self.providers: dict[str, dict] = {}
        self.file_map: dict[str, dict] = {}  # 本地缓存，通过 SUB 同步
        self.lock = Lock()
        self._release_callback = None  # buffer 释放回调

        self._init_sockets()
        self.running = True
        self._start_threads()

    def _init_sockets(self) -> None:
        """初始化 ZMQ sockets."""
        # DEALER socket 用于向 Metaserver 发送请求
        self.dealer_socket = self.context.socket(zmq.DEALER)
        self.dealer_socket.connect(self.coord_addr)
        self.logger.info("DEALER 连接: %s", self.coord_addr)

        # SUB socket 用于接收 Metaserver 的广播
        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.connect(self.sync_addr)
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
        self.logger.info("SUB 连接: %s", self.sync_addr)

    def _start_threads(self) -> None:
        """启动同步线程接收广播."""
        self.sync_thread = Thread(target=self._sync_handler, daemon=True)
        self.sync_thread.start()

    def _sync_handler(self) -> None:
        """接收 Metaserver 广播的同步消息."""
        self.logger.info("元数据同步线程启动")
        while self.running:
            try:
                msg = self.sub_socket.recv_json()
                self.logger.debug("SUB 收到消息: %s", msg)
                self._process_sync_msg(msg)
            except zmq.ZMQError as exc:
                if self.running:
                    self.logger.error("同步消息异常: %s", exc)
            except Exception as exc:
                self.logger.error("同步处理异常: %s", exc, exc_info=True)

    def _process_sync_msg(self, msg: dict) -> None:
        with self.lock:
            msg_type = msg.get("type")
            self.logger.debug("处理同步消息: type=%s, msg=%s", msg_type, msg)
            if msg_type == "register":
                self.providers[msg["host"]] = {"heartbeat": msg["timestamp"], "load": 0}
                self.logger.info("发现Provider: %s", msg["host"])
            elif msg_type == "unregister":
                if msg["host"] in self.providers:
                    del self.providers[msg["host"]]
                    self.logger.info("Provider注销: %s", msg["host"])
            elif msg_type == "heartbeat":
                if msg["host"] in self.providers:
                    self.providers[msg["host"]]["heartbeat"] = msg["timestamp"]
            elif msg_type == "file_register":
                file_key = msg.get("file_key", "")
                metadata = {
                    "object_type": msg.get("object_type", ""),
                    "data_size": msg.get("data_size", msg.get("file_size", 0)),
                    "tensor_shape": msg.get("tensor_shape", ()),
                    "tensor_dtype": msg.get("tensor_dtype"),
                    "buffer_ptr": msg.get("buffer_ptr"),
                }
                self.file_map[file_key] = {
                    "host": msg["host"],
                    "metadata": metadata,
                }
            elif msg_type == "file_unregister":
                file_key = msg.get("file_key")
                was_present = file_key in self.file_map
                if was_present:
                    del self.file_map[file_key]
                else:
                    self.logger.debug(
                        "file_unregister: file_key='%s' 不在本地 file_map", file_key
                    )
                # 调用释放回调 (如果本地持有该 buffer)
                if self._release_callback:
                    try:
                        self._release_callback(file_key)
                    except Exception as e:
                        self.logger.debug("释放 buffer '%s' 时: %s", file_key, e)
            elif msg_type == "load_update":
                host = msg["host"]
                if host in self.providers:
                    self.providers[host]["load"] = max(
                        0, self.providers[host]["load"] + msg.get("delta", 0)
                    )

    def publish(self, payload: dict) -> bool:
        """发布广播消息，通过 DEALER 发送到 Metaserver.

        Returns:
            bool: 发布是否成功
        """
        try:
            self.logger.debug("发送 publish 请求, type=%s", payload.get("type"))
            request = json.dumps({"type": "publish", "payload": payload}).encode(
                "utf-8"
            )
            self.dealer_socket.send_multipart([b"", request])

            # 等待 Metaserver 确认
            if self.dealer_socket.poll(timeout=3000):
                frames = self.dealer_socket.recv_multipart()
                resp_data = frames[1] if len(frames) >= 2 else frames[0]
                resp = json.loads(resp_data.decode("utf-8"))
                if resp.get("code") != 0:
                    self.logger.error("Metaserver publish 失败: %s", resp.get("msg"))
                    return False
                self.logger.debug("Metaserver publish 成功")
                return True
            else:
                self.logger.error("publish 请求超时，Metaserver 未响应")
                return False
        except Exception as exc:
            self.logger.error("发布消息失败: %s", exc)
            return False

    # MetadataStore 接口实现
    def register_provider(self, host: str) -> None:
        """注册 Provider 节点."""
        self.publish({"type": "register", "host": host, "timestamp": time.time()})
        with self.lock:
            self.providers[host] = {"heartbeat": time.time(), "load": 0}

    def unregister_provider(self, host: str) -> None:
        """注销 Provider 节点."""
        self.publish({"type": "unregister", "host": host, "timestamp": time.time()})
        with self.lock:
            if host in self.providers:
                del self.providers[host]

    def update_heartbeat(self, host: str) -> None:
        """更新本地记录的心跳时间."""
        with self.lock:
            if host in self.providers:
                self.providers[host]["heartbeat"] = time.time()

    def register_file(self, file_key: str, host: str, metadata: dict) -> bool:
        """注册文件并广播.

        Returns:
            bool: 注册是否成功
        """
        self.logger.info("register_file 调用: file_key='%s', host='%s'", file_key, host)
        msg = {
            "type": "file_register",
            "host": host,
            "timestamp": time.time(),
            **metadata,
            "file_key": file_key,  # 放在最后，确保不被 metadata 覆盖
        }
        success = self.publish(msg)
        if success:
            with self.lock:
                self.file_map[file_key] = {"host": host, "metadata": metadata}
        return success

    def unregister_file(self, file_key: str) -> None:
        """注销文件并广播 (仅用于本地 put 后清理, 直接广播)."""
        msg = {
            "type": "file_unregister",
            "file_key": file_key,
            "timestamp": time.time(),
        }
        self.publish(msg)
        with self.lock:
            if file_key in self.file_map:
                del self.file_map[file_key]

    def delete_file(self, file_key: str) -> bool:
        """
        删除文件 (发送请求到 Metaserver, 由 Metaserver 广播 unregister).

        Returns:
            bool: 删除是否成功
        """
        try:
            request = json.dumps({"type": "delete_file", "key": file_key}).encode(
                "utf-8"
            )
            self.dealer_socket.send_multipart([b"", request])

            if self.dealer_socket.poll(timeout=5000):  # 5s 超时
                frames = self.dealer_socket.recv_multipart()
                resp_data = frames[1] if len(frames) >= 2 else frames[0]
                resp = json.loads(resp_data.decode("utf-8"))
                if resp.get("success"):
                    self.logger.info("delete_file: 文件 %s 已删除", file_key)
                    return True
                self.logger.error("delete_file 失败: %s", resp.get("msg"))
            else:
                self.logger.error("delete_file 超时")
        except Exception as exc:
            self.logger.error("delete_file 异常: %s", exc)
        return False

    def delete_prefix(self, prefix: str) -> bool:
        """根据前缀删除文件 (暂未实现)."""
        pass

    def delete_prefix_batch(self, prefixes: list[str]) -> dict[str, bool]:
        """批量根据前缀删除文件 (暂未实现)."""
        pass

    def set_release_callback(self, callback) -> None:
        """设置 buffer 释放回调函数."""
        self._release_callback = callback

    def check_connection(self, timeout_ms: int = 3000) -> bool:
        """
        检查与 Metaserver 的连通性.

        Args:
            timeout_ms: 超时时间（毫秒）

        Returns:
            bool: 连通返回 True，否则 False
        """
        try:
            request = json.dumps({"type": "list_files"}).encode("utf-8")
            self.dealer_socket.send_multipart([b"", request])

            if self.dealer_socket.poll(timeout=timeout_ms):
                frames = self.dealer_socket.recv_multipart()
                resp_data = frames[1] if len(frames) >= 2 else frames[0]
                resp = json.loads(resp_data.decode("utf-8"))
                return resp.get("code") == 0
            else:
                self.logger.warning("check_connection 超时，Metaserver 未响应")
                return False
        except Exception as exc:
            self.logger.error("check_connection 异常: %s", exc)
            return False

    def clear_files(self) -> dict:
        """
        清空所有文件元数据.

        Returns:
            dict: {"success": bool, "cleared": int, "failed": list[str]}
        """
        try:
            request = json.dumps({"type": "clear_files"}).encode("utf-8")
            self.dealer_socket.send_multipart([b"", request])

            if self.dealer_socket.poll(timeout=10000):  # 10s 超时
                frames = self.dealer_socket.recv_multipart()
                resp_data = frames[1] if len(frames) >= 2 else frames[0]
                resp = json.loads(resp_data.decode("utf-8"))
                if resp.get("code") == 0:
                    self.logger.info(
                        "clear_files: 成功清空 %d 个文件, 失败 %d 个",
                        resp.get("cleared", 0),
                        len(resp.get("failed", [])),
                    )
                    return resp
                self.logger.error("clear_files 失败: %s", resp.get("msg"))
            else:
                self.logger.error("clear_files 超时")
        except Exception as exc:
            self.logger.error("clear_files 异常: %s", exc)

        return {"success": False, "cleared": 0, "failed": []}

    def query_file(self, file_key: str) -> dict | None:
        """向 Coordinator 查询文件信息."""
        try:
            request = json.dumps({"type": "query_file", "key": file_key}).encode(
                "utf-8"
            )
            self.dealer_socket.send_multipart([b"", request])
            frames = self.dealer_socket.recv_multipart()
            payload = frames[1] if len(frames) >= 2 else frames[0]
            resp = json.loads(payload.decode("utf-8"))
            if resp.get("code") == 0:
                return resp["data"]
            # key 不存在是正常情况，不打 GGG
            self.logger.debug("查询 '%s': %s", file_key, resp.get("msg"))
            return None
        except Exception as exc:
            self.logger.error("查询异常: %s", exc, exc_info=True)
            return None

    def update_load(self, host: str, delta: int) -> None:
        """更新本地记录的负载."""
        with self.lock:
            if host in self.providers:
                self.providers[host]["load"] = max(
                    0, self.providers[host]["load"] + delta
                )

    def list_files(self) -> dict[str, dict]:
        """向 Metaserver 查询所有文件信息."""
        try:
            request = json.dumps({"type": "list_files"}).encode("utf-8")
            self.dealer_socket.send_multipart([b"", request])

            if self.dealer_socket.poll(timeout=3000):  # 3s 超时
                frames = self.dealer_socket.recv_multipart()
                payload = frames[1] if len(frames) >= 2 else frames[0]
                resp = json.loads(payload.decode("utf-8"))
                if resp.get("code") == 0:
                    return resp["data"]
                self.logger.error("list_files 失败: %s", resp.get("msg"))
            else:
                self.logger.warning("list_files 超时, 返回本地缓存")
        except Exception as exc:
            self.logger.error("list_files 异常: %s", exc)

        # 降级返回本地缓存
        with self.lock:
            return dict(self.file_map)

    def close(self) -> None:
        """关闭 ZMQ 上下文和线程."""
        self.running = False
        time.sleep(0.5)
        self.context.term()
        self.logger.info("ZMQ Metadata 关闭")
