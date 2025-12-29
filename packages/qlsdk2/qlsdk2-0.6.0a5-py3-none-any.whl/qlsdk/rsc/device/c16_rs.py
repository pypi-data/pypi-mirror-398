
from multiprocessing import Queue
from threading import Thread
from time import sleep, time_ns
from typing import Any, Dict, Literal

from loguru import logger
from qlsdk.persist import RscEDFHandler
from qlsdk.rsc.device.device_factory import DeviceFactory
from qlsdk.rsc.interface import IDevice
from qlsdk.rsc.command import *
from qlsdk.rsc.device.base import QLBaseDevice

'''
    C16RS设备类，继承自QLBaseDevice
    提供设备特定的属性和方法，包括设备类型、采集参数设置、电刺激参
'''
class C16RS(QLBaseDevice):
    
    device_type = 0x339  # C16RS设备类型标识符
    
    def __init__(self, socket):
        
        super().__init__(socket)
        # 存储通道反向映射位置值
        self._reverse_ch_pos  = None    
        
        self.channel_name_mapping = {
            "FP1": 1, 
            "FP2": 2, 
            "C3": 3, 
            "C4": 4, 
            "O1": 5, 
            "O2": 6, 
            "CZ": 7, 
            "T7": 8,
            "T8": 9, 
            "M1": 10, 
            "M2": 11, 
            "F3": 12, 
            "F4": 13, 
            "FZ": 14, 
            "F7": 15, 
            "F8": 16, 
            "PZ": 17, 
            "P3": 18, 
            "P7": 19, 
            "P4": 20, 
            "P8": 21,
            "T3": 8,
            "T4": 9, 
            "A1": 10, 
            "A2": 11, 
        }
        
        self.channel_mapping = {
            "1": 59, 
            "2": 60, 
            "3": 53, 
            "4": 50, 
            "5": 51, 
            "6": 64, 
            "7": 49, 
            "8": 63,
            "9": 24, 
            "10": 14, 
            "11": 10, 
            "12": 11, 
            "13": 57, 
            "14": 16, 
            "15": 55, 
            "16": 15, 
            "17": 40, 
            "18": 37, 
            "19": 34, 
            "20": 18, 
            "21": 47
        }
        
        self.channel_display_mapping = {
            59: 1, 
            60: 2, 
            53: 3, 
            50: 4, 
            51: 5, 
            64: 6, 
            49: 7, 
            63: 8,
            24: 9, 
            14: 10, 
            10: 11, 
            11: 12, 
            57: 13, 
            16: 14, 
            55: 15, 
            15: 16, 
            40: 17, 
            37: 18, 
            34: 19, 
            18: 20, 
            47: 21
        }
    
    
    @classmethod
    def from_parent(cls, parent:IDevice) -> IDevice:
        rlt = cls(parent.socket)
        rlt.device_id = parent.device_id
        rlt._device_no = parent.device_no
        return rlt  
        
    def init_edf_handler(self):
        self._edf_handler = RscEDFHandler(self.sample_rate,  self.sample_range * 1000 , - self.sample_range * 1000, self.resolution, record_duration = self._record_duration)  
        self._edf_handler.set_device_type(self.device_type)
        self._edf_handler.set_device_no(self.device_no)
        self._edf_handler.set_storage_path(self._storage_path)
        self._edf_handler.set_file_prefix(self._file_prefix if self._file_prefix else 'C16R')
            
    # 设置刺激参数
    def set_stim_param(self, param):
        self.stim_paradigm = param
    
    # 设置采集参数
    def set_acq_param(self, channels, sample_rate = 500, sample_range = 188):
        # 保存原始通道参数
        self._acq_param["original_channels"] = channels
        
        # 名称转换为数字通道  
        channels = [self.channel_name_mapping.get(str(i).upper(), i) for i in channels]
        
        # 根据映射关系做通道转换-没有映射的默认到第一个通道
        # 先设置不存在的通道为-1，再把-1替换为第一个通道，避免第一个通道也不合法的情况
        channels = [self.channel_mapping.get(str(i), -1) for i in channels]
        channels = [i if i != -1 else channels[0] for i in channels]
                
        # 更新采集参数
        self._acq_param["channels"] = channels
        self._acq_param["sample_rate"] = sample_rate
        self._acq_param["sample_range"] = sample_range
        self._acq_channels = channels
        self._sample_rate = sample_rate
        self._sample_range = sample_range
        
        logger.debug(f"C16RS: set_acq_param: {self._acq_param}")   
        
        # 参数改变后，重置通道位置映射
        self._reverse_ch_pos  = None  
    
    # 信号数据转换(默认不处理)
    def _signal_wrapper(self, data: RscPacket):
        if data is None:
            return
        # 根据映射关系做通道转换-（注意数据和通道的一致性）
        # data.channels = [self.channel_display_mapping.get(i, i) for i in data.channels]
        
        # 升级为类变量，减少计算
        if self._reverse_ch_pos is None:
            self._reverse_ch_pos = map_indices(self._acq_param["channels"], data.channels)
        
        # 更新通道（数据）顺序和输入一致
        data.channels = self._acq_param["original_channels"]
        data.eeg = [data.eeg[i] for i in self._reverse_ch_pos]
        
        
def map_indices(A, B):
    """
    
    参数:
        A: 源数组（无重复值）
        B: 目标数组（无重复值）
    
    返回:
        C: 与A长度相同的数组，元素为A中对应值在B中的索引（不存在则为-1）
    """
    # 创建B的值到索引的映射字典（O(n)操作）
    b_map = {value: idx for idx, value in enumerate(B)}
    
    # 遍历A，获取每个元素在B中的位置（O(m)操作）
    return [b_map.get(a, -1) for a in A]
                
    
# Register the C16RS device with the DeviceFactory
DeviceFactory.register(C16RS.device_type, C16RS) 
    
    