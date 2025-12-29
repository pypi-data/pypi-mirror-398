from multiprocessing import Queue
from typing import Literal
from loguru import logger
from qlsdk.sdk import LMDevice, LMPacket
import numpy as np
from qlsdk.persist import EdfHandler
import time
    
# 设备对象
class AR4(LMDevice):
    def __init__(self, box_mac:str, is_persist:bool=True, storage_path:str=None):
        # 是否持久化-保存为文件
        self._is_persist = is_persist
        self._storage_path = storage_path
        self._edf_handler = None
        
        self._recording = False
        self._record_start_time = None
        
        self._acq_info = {}
        # 订阅者列表，数值为数字信号值
        self._dig_subscriber: dict[str, Queue] = {}
        # 订阅者列表，数值为物理信号值
        self._phy_subscriber: dict[str, Queue] = {}
        
        super().__init__(box_mac)
    
    def set_storage_path(self, storage_path):
        self._storage_path = storage_path

    @property
    def device_type(self):
        return "AR4"
    
       
    def eeg_accept(self, packet):        
        if len(self._dig_subscriber) > 0 or len(self._phy_subscriber) > 0:            
            for consumer in self._dig_subscriber.values():
                consumer.put(packet)
             
            if len(self._phy_subscriber) > 0:
                logger.debug(f"dig data eeg: {packet.eeg}")
                logger.debug(f"dig data acc: {packet.acc}")
                packet.eeg = self.eeg2phy(np.array(packet.eeg))
                packet.acc = self.acc2phy(np.array(packet.acc))
                logger.debug(f"phy data eeg: {packet.eeg}")
                logger.debug(f"phy data acc: {packet.acc}")
                for consumer2 in self._phy_subscriber.values():
                    consumer2.put(packet)
            
            if self._is_persist:
                if self._edf_handler is None:
                    self.start_record()
                    self._recording = True
                    self._record_start_time = packet.time_stamp
                    logger.info(f"开始记录数据: {self.box_mac}")
            
                # 处理数据包
                self._edf_handler.append(packet)
    
    def start_record(self):
        if self._is_persist:
            if self._edf_handler is None:
                self._edf_handler = EdfHandler(self.sample_frequency, self.eeg_phy_max, self.eeg_phy_min, self.eeg_dig_max, self.eeg_dig_min, storage_path=self._storage_path)
                self._edf_handler.set_device_type(self.device_type)
                self._edf_handler.set_storage_path(self._storage_path)
                
    def stop_record(self):
        if self._edf_handler:
            # 等待设备端数据传输完成
            time.sleep(0.5)
            # 添加结束标识
            self._edf_handler.append(None)
            self._edf_handler = None
            self._recording = False
            logger.info(f"停止记录数据: {self.box_mac}")
            
    def trigger(self, desc):
        if self._edf_handler:
            self._edf_handler.trigger(desc)
            
    # 订阅推送消息 
    def subscribe(self, topic: str = None, q: Queue = Queue(), value_type: Literal['phy', 'dig'] = 'phy') -> tuple[str, Queue]:
        if topic is None:
            topic = f"msg_{self.box_mac}"
        
        if value_type == 'dig':
            if topic in list(self._dig_subscriber.keys()):  
                logger.warning(f"ar4 {self.box_mac} 订阅主题已存在: {topic}")
                return topic, self._dig_subscriber[topic]
            self._dig_subscriber[topic] = q
        else:
            if topic in list(self._phy_subscriber.keys()):  
                logger.warning(f"ar4 {self.box_mac} 订阅主题已存在: {topic}")
                return topic, self._phy_subscriber[topic]
            self._phy_subscriber[topic] = q
        
        return topic, q    
    
    def eeg2phy(self, digtal):
        # 向量化计算（自动支持广播）
        return super().eeg2phy(digtal)
    
    def acc2phy(self, digtal):
        return super().eeg2phy(digtal)
            
class X8Packet(LMPacket):
    def __init__(self, data: bytes):
        super().__init__(data)
        self._data = data
        self._head = None
        self._body = None
        
    @property
    def head(self):
        return self._head
    
    @property
    def body(self):
        return self._body
    
    def parse(self):
        # 解析数据包头部和数据体
        if len(self._data) < 4:
            logger.error(f"数据包长度不足: {len(self._data)}")
            return False
        
        # 解析头部和数据体
        self._head = self._data[:4]
        self._body = self._data[4:]
        
        return True