"""
TCP Transport 实现模块.

该模块实现了基于 TCP 协议的传输层 `TCPTransport`。
它提供了一个轻量级的、基于 Socket 的数据传输实现，适用于不支持 RDMA 的环境或测试场景。
实现了基本的握手、长度前缀分包和数据传输逻辑。
"""

from __future__ import annotations

import json
import socket
import threading
from typing import Any, Dict, Optional

import numpy as np

from ..core import TransferRequest, Transport
from ..utils.logger import LoggerManager


class TCPTransport(Transport):
    """轻量级 TCP 传输实现, 通过简易请求/响应协议同步数据."""

    def __init__(self) -> None:
        self._logger = LoggerManager.get_logger("tcp-transport")
        self._local_addr: Optional[str] = None
        self._storage: Dict[str, bytes] = {}
        self._lock = threading.Lock()
        self._server_socket: Optional[socket.socket] = None
        self._running = False

    def initialize(self, local_addr: str, device: str = "") -> bool:
        """初始化 TCP 监听服务."""
        try:
            host, port = local_addr.split(":")
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind((host, int(port)))
            self._server_socket.listen(64)
            self._local_addr = local_addr
            self._running = True
            threading.Thread(target=self._serve_loop, daemon=True).start()
            self._logger.info("TCP 传输监听启动, 地址: %s", local_addr)
            return True
        except Exception as exc:
            self._logger.error("TCP 初始化失败: %s", exc, exc_info=True)
            return False

    # Provider 侧: 存储数据
    def send(self, remote_addr: str, request: TransferRequest, data: Any) -> bool:
        try:
            file_key = request.metadata.get("file_key")
            if not file_key:
                raise ValueError("TransferRequest.metadata 必须包含 file_key")
            blob = self._normalize_bytes(data)
            with self._lock:
                self._storage[file_key] = blob
            request.data_size = len(blob)
            self._logger.debug("TCP 缓存数据: key=%s size=%d", file_key, len(blob))
            return True
        except Exception as exc:
            self._logger.error("TCP send 失败: %s", exc, exc_info=True)
            return False

    # Consumer 侧: 通过 TCP 连接获取数据
    def recv(self, request: TransferRequest, remote_addr: Optional[str] = None) -> Any:
        if remote_addr is None:
            raise ValueError("TCP recv 需要 remote_addr")
        file_key = request.metadata.get("file_key")
        if not file_key:
            raise ValueError("TransferRequest.metadata 缺少 file_key")

        host, port = remote_addr.split(":")
        try:
            with socket.create_connection((host, int(port)), timeout=30) as conn:
                self._send_line(conn, json.dumps({"key": file_key}))
                header = json.loads(self._recv_line(conn))
                if header.get("status") != "ok":
                    raise RuntimeError(header.get("msg", "未知错误"))
                remaining = int(header.get("data_size", 0))
                chunks = []
                while remaining > 0:
                    chunk = conn.recv(min(remaining, 65536))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    remaining -= len(chunk)
                data = b"".join(chunks)
                if len(data) != int(header.get("data_size", 0)):
                    raise RuntimeError("TCP 数据长度不匹配")
                return data
        except Exception as exc:
            self._logger.error("TCP recv 失败: %s", exc, exc_info=True)
            return None

    def get_local_addr(self) -> str:
        if not self._local_addr:
            raise RuntimeError("TCPTransport 尚未初始化")
        return self._local_addr

    def release(self, key: str) -> None:
        with self._lock:
            self._storage.pop(key, None)

    # ------------------------------------------------------------------
    # 内部实现
    # ------------------------------------------------------------------
    def _serve_loop(self) -> None:
        assert self._server_socket is not None
        while self._running:
            try:
                conn, _ = self._server_socket.accept()
                threading.Thread(
                    target=self._handle_conn, args=(conn,), daemon=True
                ).start()
            except OSError:
                break
            except Exception as exc:
                self._logger.error("TCP 接受连接失败: %s", exc, exc_info=True)

    def _handle_conn(self, conn: socket.socket) -> None:
        with conn:
            try:
                payload = json.loads(self._recv_line(conn))
                key = payload.get("key")
                if not key:
                    raise ValueError("请求缺少 key")
                with self._lock:
                    blob = self._storage.get(key)
                if blob is None:
                    self._send_line(
                        conn, json.dumps({"status": "error", "msg": "NOT_FOUND"})
                    )
                    return
                self._send_line(
                    conn,
                    json.dumps({"status": "ok", "data_size": len(blob)}),
                )
                conn.sendall(blob)
            except Exception as exc:
                self._logger.error("TCP 处理连接失败: %s", exc, exc_info=True)

    def _recv_line(self, conn: socket.socket) -> str:
        buffer = bytearray()
        while True:
            chunk = conn.recv(1)
            if not chunk:
                break
            if chunk == b"\n":
                break
            buffer.extend(chunk)
        return buffer.decode("utf-8")

    def _send_line(self, conn: socket.socket, data: str) -> None:
        conn.sendall(data.encode("utf-8") + b"\n")

    def _normalize_bytes(self, data: Any) -> bytes:
        if isinstance(data, bytes):
            return data
        if isinstance(data, bytearray):
            return bytes(data)
        if isinstance(data, memoryview):
            return data.tobytes()
        if isinstance(data, np.ndarray):
            return data.tobytes()
        tensor_fn = getattr(data, "numpy", None)
        if callable(tensor_fn):
            arr = tensor_fn()
            return np.asarray(arr).tobytes()
        raise TypeError(f"无法转换的数据类型: {type(data)}")
