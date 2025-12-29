from multiprocessing import Lock
from qlsdk.rsc.interface import IDevice, IParser

from loguru import logger
from threading import Thread
from time import time_ns
from qlsdk.rsc.command import CommandFactory

class RSCMessageParser(IParser):
    def __init__(self, device : IDevice):
        # 待解析的数据来源于该设备
        self.device = device    
        self.running = False
        
        # 缓冲区-用于处理数据
        self.buffer:bytearray = bytearray()
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
        print(f"append value len: {len(value)}")
    def __parser__(self):
        logger.info("数据解析开始")
                
        try:
            while self.running:
                
                # 查找消息头
                while len(self.buffer) < len(self.header):
                    read_data = self.device.read_msg(1)
                    if read_data is None:
                        if self.running:
                            continue
                        else:
                            break
                    if read_data[0] == self.header[len(self.buffer)]:
                        self.buffer.extend(read_data)
                    else:
                        self.buffer.clear()
                        break            
                
                if len(self.buffer) < len(self.header):
                    continue
                
                
                # 判断消息头
                while len(self.buffer) < self.header_len:
                    read_data = self.device.read_msg(self.header_len - len(self.buffer))
                    if read_data is None:
                        if self.running:
                            continue
                        else:
                            break
                    self.buffer.extend(read_data)                    
                
                # # 移动下标(指向包长度的位置)
                # self.buffer.seek(self.start_pos + 8)
                # 包总长度
                pkg_len = int.from_bytes(self.buffer[8:12], 'little')
                # 256*32K = 8388608
                # 太长2M
                if pkg_len > 2048000:
                    print(f"error message pkg_len={pkg_len} > 1000000")
                    self.buffer.clear()
                    continue
                # 太短
                if pkg_len < self.header_len:
                    print(f"error message pkg_len={pkg_len} < {self.header_len}")
                    self.buffer.clear()
                    continue
                
                # 读取消息体
                while len(self.buffer) < pkg_len:
                    read_data = self.device.read_msg(pkg_len - len(self.buffer))
                    if read_data is None:
                        if self.running:
                            continue
                        else:
                            break
                    self.buffer.extend(read_data)
                
                if len(self.buffer) < pkg_len:
                    continue
                    
                # msg_crc = self.buffer[-2:]
                # cal_crc = (bytes_buffer, len(bytes_buffer) - 2)
                # if cal_crc != msg_crc:
                #     print(f'crc fail {cal_crc} {msg_crc}')
                # if cal_crc != msg_crc:
                #     print(f'crc fail {cal_crc} {msg_crc}')                    
                
                self.unpack(self.buffer)
                self.buffer.clear()
                
        except Exception as e:
            logger.error(f"数据解析异常: {e}")
                
        logger.info(f"数据解析结束:{self.running}")
    
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
        