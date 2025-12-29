from enum import Enum
import threading
import collections
from typing import Optional

from loguru import logger
from qlsdk.rsc.interface import IDevice, IParser
from qlsdk.rsc.command import CommandFactory

# 解析状态机
class ParserState(Enum):
    FIND_HEADER = 1
    READ_LENGTH = 2
    READ_BODY = 3

class TcpMessageParser(IParser):
    HEADER = b'\x5a\xa5'
    HEADER_LEN = 14
    MAX_PKG_LEN = 1 * 1024 * 1024        # 1 MB
    MAX_BUF_LEN = 100 * 1024 * 1024       # 10 MB
    READ_CHUNK = 4096

    def __init__(self, device: IDevice):
        self.device = device

        # 生产者-消费者缓冲区：线程安全 deque + bytearray
        self._buf = bytearray()
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)

        self._running = threading.Event()

    # ---------- 生产者 ----------
    def append(self, data: bytes) -> None:
        logger.info(f"接收数据: {data.hex()}")
        with self._not_empty:
            if len(self._buf) + len(data) > self.MAX_BUF_LEN:
                logger.warning("缓冲区超限，丢弃旧数据")
                self._buf.clear()
            self._buf.extend(data)
            self._not_empty.notify()

    # ---------- 消费者 ----------
    def start(self) -> None:
        self._running.set()
        self._thread = threading.Thread(target=self._parser_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running.clear()
        with self._not_empty:
            self._not_empty.notify_all()
        self._thread.join(timeout=1)

    # ---------- 解析主循环 ----------
    def _parser_loop(self) -> None:
        """状态机：找头 -> 读长度 -> 读体 -> 校验 -> 投递"""
        state = ParserState.FIND_HEADER
        need = len(self.HEADER)
        header_pos = 0
        pkg_len = 0
        logger.info("数据解析开始")

        while self._running.is_set():
            with self._not_empty:
                while len(self._buf) < need:
                    if not self._running.is_set():
                        return
                    self._not_empty.wait(timeout=0.1)

                view = memoryview(self._buf)  # 零拷贝视图

                if state == ParserState.FIND_HEADER:
                    # idx = view.find(self.HEADER)
                    # if idx == -1:
                    #     # 整段数据都没有头，全部丢弃
                    #     del self._buf[:len(self._buf) - 1]
                    #     continue
                    # # 去掉头部之前可能残留的脏数据
                    # del self._buf[:idx]
                    # state = 'READ_LENGTH'
                    # need = self.HEADER_LEN
                    # continue
                    with self._not_empty:
                        while len(view) < need:
                            if not self._running.is_set():
                                return
                            self._not_empty.wait(timeout=0.1)

                    # 1. 用 bytearray.find 找包头
                    idx = view.find(self.HEADER)
                    if idx == -1:
                        # 没有包头，保留最后 len(self.HEADER)-1 个字节即可
                        del self._buf[:-len(self.HEADER) + 1 or None]
                        continue

                    # 2. 去掉头部的脏数据
                    del self._buf[:idx]
                    state = 'READ_LENGTH'
                    need = self.HEADER_LEN
                    continue

                if state == 'READ_LENGTH':
                    pkg_len = int.from_bytes(view[8:12], 'little')
                    if pkg_len < self.HEADER_LEN or pkg_len > self.MAX_PKG_LEN:
                        logger.warning(f"非法包长度 {pkg_len}，丢弃")
                        del self._buf[:1]        # 跳过当前头继续找下一个
                        state = 'FIND_HEADER'
                        need = len(self.HEADER)
                        continue

                    state = 'READ_BODY'
                    need = pkg_len
                    continue

                if state == 'READ_BODY':
                    packet = bytes(view[:pkg_len])      # 拷贝一份完整包
                    del self._buf[:pkg_len]             # 从缓冲区删除
                    self._dispatch(packet)
                    state = 'FIND_HEADER'
                    need = len(self.HEADER)

    # ---------- 业务分发 ----------
    def _dispatch(self, packet: bytes) -> None:
        try:
            cmd = int.from_bytes(packet[12:14], 'little')
            cls = CommandFactory.create_command(cmd)
            inst = cls(self.device)
            inst.parse_body(packet[self.HEADER_LEN:-2])  # 去掉头尾
        except Exception as exc:
            logger.exception(f"解析失败: {exc}")

    # ---------- 工具 ----------
    def set_device(self, device: IDevice) -> None:
        self.device = device