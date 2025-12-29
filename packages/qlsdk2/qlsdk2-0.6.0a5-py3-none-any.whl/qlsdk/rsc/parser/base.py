from io import BytesIO
from multiprocessing import Lock
import time
from qlsdk.rsc.interface import IDevice, IParser

from loguru import logger
from threading import Thread
from time import time_ns
from qlsdk.rsc.command import CommandFactory

class TcpMessageParser(IParser):
    def __init__(self, device : IDevice):
        # 待解析的数据来源于该设备
        self.device = device    
        self.running = False
        
        # 网络实时数据缓存，选用BytesIO
        # 临时缓冲区-用于接收数据
        self.cache = BytesIO()
        # 缓冲区-用于处理数据
        self.buffer = BytesIO()
        # 读写锁-用于临时缓冲区（避免读写冲突）
        self._lock = Lock()
        
    @property
    def header(self):
        return b'\x5A\xA5'
    
    @property
    def header_len(self):
        return 14
    
    @property
    def cmd_pos(self):
        return 12
    
    def set_device(self, device):
        self.device = device
        
    def append(self, value):
        # self.cache.write(buffer)
        with self._lock:
            self.cache.write(value)
            
    def __parser__(self):
        logger.info("数据解析开始")
        
        # 告警阈值（10M)
        warn_len = 10 * 1024 * 1024
        
        try:
            while self.running:
                buf_len = get_len(self.buffer)
                
                if buf_len < self.header_len:
                    logger.trace(f"等待数据中...: expect: {self.header_len}, actual: {buf_len}")
                    if not self.__fill_from_cache():
                        time.sleep(0.1)
                        continue
                    
                if buf_len > warn_len:
                    logger.warning(f"操作区缓存数据过大: {buf_len} bytes, 可能存在数据丢失风险")
                    
                start_pos = self.buffer.tell()
                head = self.buffer.read(2)
                if head != self.header:
                    logger.debug(f"数据包头部不匹配: {head.hex()}, 期望: {self.header.hex()},继续查找...")
                    self.buffer.seek(start_pos + 1)  # 移动到下一个字节
                    continue
                
                # 移动下标(指向包长度的位置)
                self.buffer.seek(start_pos + 8)
                # 包总长度
                pkg_len = int.from_bytes(self.buffer.read(4), 'little')
                buf_len = get_len(self.buffer)
                
                # 直接等待长度足够（如果从头开始判断，因为逻辑相同，所以会执行一样的操作）
                while buf_len < pkg_len:
                    logger.trace(f"操作区缓存数据不足: expect: {pkg_len}, actual: {buf_len}, 等待数据...")
                    if self.__fill_from_cache():
                        buf_len = get_len(self.buffer)
                        continue
                    else:
                        time.sleep(0.05)
                        
                # 读取剩余数据
                self.buffer.seek(pkg_len)
                tmp = self.buffer.read()    
                
                # 读取当前数据包         
                self.buffer.seek(start_pos)
                pkg = self.buffer.read(pkg_len)
                
                # 清空操作区缓存(truncate会保留内存，重新初始化）
                self.buffer = BytesIO()
                if len(tmp) > 0:
                    self.buffer.write(tmp)                
                self.buffer.seek(0)
                
                self.unpack(pkg)
        except Exception as e:
            logger.error(f"数据解析异常: {e}")
                
        logger.info(f"数据解析结束:{self.running}")
    
    # 填充操作区缓存
    def __fill_from_cache(self) -> bool:   
        result = False
        
        cur_pos = self.buffer.tell()
        # 移动到操作区缓存末尾，内容追加到缓冲区尾部
        self.buffer.seek(0,2)
        len = self.buffer.tell()
        # 操作缓冲区
        with self._lock: 
            cache_len = get_len(self.cache)
            
            # 临时缓冲区只要有数据，就写入操作缓冲区（避免分片传输导致数据不完整）
            if cache_len > 0:      
                if len == 0:
                    self.buffer = self.cache
                    cur_pos = 0
                else: 
                    self.buffer.write(self.cache.getvalue())
                self.cache = BytesIO()  # 清空缓冲区
                result = True
            
        self.buffer.seek(cur_pos)  # 恢复到原位置
        
        return result
    
    def unpack(self, packet):        
        # 提取指令码
        cmd_code = int.from_bytes(packet[self.cmd_pos : self.cmd_pos + 2], 'little')
        cmd_class = CommandFactory.create_command(cmd_code)
        instance = cmd_class(self.device)
        instance.parse_body(packet[self.header_len:-2])
        return instance
            
    def start(self):
        self.running = True
        parser = Thread(target=self.__parser__, daemon=True)
        parser.start()
        
    def stop(self):
        self.running = False
        
# 工具方法
def get_len(buf: BytesIO) -> int:
        if buf is None:
            return 0
        cur_pos = buf.tell()
        buf.seek(0, 2)  # 移动到操作区缓存末尾
        len = buf.tell()
        buf.seek(cur_pos)  # 恢复到原位置
        return len
    