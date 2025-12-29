from datetime import datetime
import os
from threading import Lock
from loguru import logger
import numpy as np

from qlsdk.core.entity import RscPacket
from qlsdk.persist.rsc_edf import RscEDFHandler
from qlsdk.persist.stream import EDF_FILE_TYPE, EDFStreamWriter


def intersection_positions(A, B):
    setB = set(B)
    seen = set()
    return [idx for idx, elem in enumerate(A) 
            if elem in setB and elem not in seen and not seen.add(elem)]

# 用作数据结构一致化处理，通过调用公共类写入edf文件
# 入参包含写入edf的全部前置参数
# 实时数据包为个性化数据包，含有eeg数据部分
class ARSKindlingEDFHandler(object):
    '''
        Rsc EDF Handler
        处理EDF文件的读写
        RSC设备通道数根据选择变化，不同通道采样频率相同
        eeg_sample_rate: 采样频率
        physical_max: 物理最大值 (uV)   
        physical_min: 物理最小值 (uV)
        resolution: 分辨率
        storage_path: 存储路径        
        
        @author: qlsdk
        @since: 0.4.0
    '''
    def __init__(self, eeg_sample_rate, physical_max, physical_min, resolution=24, storage_path = None):
        # edf文件参数
        self.physical_max = physical_max
        self.physical_min = physical_min
        self.digital_max = 8388607 if resolution == 24 else 32767
        self.digital_min = -8388607 if resolution == 24 else - 32768
        self.file_type = EDF_FILE_TYPE["bdf"] if resolution == 24 else EDF_FILE_TYPE["edf"]
        # 点分辨率
        self.resolution = resolution
        # eeg通道数
        self.channels = None
        # eeg采样率
        self.sample_rate = eeg_sample_rate
        # bytes per second
        self.bytes_per_second = 0
        self._edf_writer = None
        self._cache2 = tuple()
        self._recording = False
        self._edf_writer = None
        self.annotations = None
        # 每个数据块大小
        self._chunk = np.array([])
        self._duration = 0
        self._points = 0
        self._first_pkg_id = None
        self._last_pkg_id = None
        self._first_timestamp = None
        self._start_time = None
        self._end_time = None
        self._patient_code = "patient_code"
        self._patient_name = "patient_name"
        self._device_type = "24130032"
        self._device_no = "24130032"
        self._total_packets = 0
        self._lost_packets = 0
        self._storage_path = storage_path
        self._edf_writer_thread = None
        self._file_prefix = None
        
        # 癫痫造模仪1对4， 这个是固定模式，写死，规则随设备
        self._edf_handler = {}
        self._edf_Handler_A = None
        self._edf_Handler_B = None  
        self._edf_Handler_C = None
        self._edf_Handler_D = None
        
        self._channel_spilt = {
            "A" : [49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62],
            "B" : [33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46],
            "C" : [17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30],
            "D" : [7, 8, 5, 6, 3, 4, 1, 2, 9, 10, 11, 12, 13, 14],
        }
        
        self._channel_mapping = {
            1: "D7", 
            2: "D8",
            3: "D5", 
            4: "D6",
            5: "D3", 
            6: "D4",
            7: "D1", 
            8: "D2",
            9: "D9", 
            10: "D10",
            11: "D11", 
            12: "D12",
            13: "D13", 
            14: "D14",
            
            17: "C7", 
            18: "C8",
            19: "C5", 
            20: "C6",
            21: "C3", 
            22: "C4",
            23: "C1", 
            24: "C2",
            25: "C9", 
            26: "C10",
            27: "C11", 
            28: "C12",
            29: "C13", 
            30: "C14",
            
            33: "B7", 
            34: "B8",
            35: "B5", 
            36: "B6",
            37: "B3", 
            38: "B4",
            39: "B1", 
            40: "B2",
            41: "B9", 
            42: "B10",
            43: "B11", 
            44: "B12",
            45: "B13", 
            46: "B14",
            
            49: "A7", 
            50: "A8",
            51: "A5", 
            52: "A6",
            53: "A3", 
            54: "A4",
            55: "A1", 
            56: "A2",
            57: "A9", 
            58: "A10",
            59: "A11", 
            60: "A12",
            61: "A13", 
            62: "A14"
        }
        
        self._lock = Lock()
        
    @property
    def file_name(self): 
        suffix = "bdf" if self.resolution == 24 else "edf"
        
        # 文件名称
        file_name = f"{self._file_prefix}_{self._device_no}_{self._start_time.strftime('%y%m%d%H%I%M')}.{suffix}" if self._file_prefix else f"{self._device_no}_{self._start_time.strftime('%y%m%d%H%I%M')}.{suffix}"
        
        if self._storage_path:
            try:
                # 自动创建目录，存在则忽略
                os.makedirs(self._storage_path, exist_ok=True)  
                
                return f"{self._storage_path}/{file_name}"
            except Exception as e:
                logger.error(f"创建目录[{self._storage_path}]失败: {e}")            
        
        return file_name
    
    def set_device_type(self, device_type):
        if device_type == 0x39:
            self._device_type = "C64RS"
        elif device_type == 0x40:
            self._device_type = "LJ64S1"
        else:
            self._device_type = hex(device_type)
        
    def set_device_no(self, device_no):
        self._device_no = device_no
        
    def set_storage_path(self, storage_path):
        self._storage_path = storage_path
        
    def set_file_prefix(self, file_prefix):
        self._file_prefix = file_prefix
        
    def set_patient_code(self, patient_code):
        self._patient_code = patient_code
        
    def set_patient_name(self, patient_name):
        self._patient_name = patient_name
    
    def write(self, packet: RscPacket):
        # logger.trace(f"packet: {packet}")    
        if packet is None:
            # self._edf_writer_thread.stop_recording()
            for k in self._edf_handler.keys():
                self._edf_handler[k].append(None)
            return
         
        #按分区写入数据
        
        for k in self._channel_spilt.keys():      
            logger.info(f'分区{k}, {self._channel_spilt[k]}')      
            p = packet
            self.writeA(p, self._channel_spilt[k], k)
    
        # with self._lock:
        #     if self.channels is None:
        #         logger.info(f"开始记录数据到文件...")
        #         self.channels = packet.channels
        #         self._first_pkg_id = packet.pkg_id if self._first_pkg_id is None else self._first_pkg_id
        #         self._first_timestamp = packet.time_stamp if self._first_timestamp is None else self._first_timestamp
        #         self._start_time = datetime.now()
        #         logger.info(f"第一个包id: {self._first_pkg_id }, 时间戳:{self._first_timestamp}， 当前时间:{datetime.now().timestamp()}  offset: {datetime.now().timestamp() - self._first_timestamp}")
                
        #     if self._last_pkg_id and self._last_pkg_id != packet.pkg_id - 1:  
        #         self._lost_packets += packet.pkg_id - self._last_pkg_id - 1
        #         logger.warning(f"数据包丢失: {self._last_pkg_id} -> {packet.pkg_id}, 丢包数: {packet.pkg_id - self._last_pkg_id - 1}")
                
        #     self._last_pkg_id = packet.pkg_id
        #     self._total_packets += 1
            
        #     if self._edf_writer_thread is None:
        #         self._edf_writer_thread = EDFStreamWriter(self.channels, self.sample_rate, self.physical_max, self.physical_min, self.file_type, self.file_name)
        #         self._edf_writer_thread.set_start_time(self._start_time)
        #         self._edf_writer_thread.start()
        #         logger.info(f"开始写入数据: {self.file_name}")
                
        #     self._edf_writer_thread.append(packet.eeg)
     
    def writeA(self, packet: RscPacket, channel_filter, name='A'):
        # 参数检查
        if packet is None or channel_filter is None:
            logger.warning("空数据，忽略")
            return
        
        channel_pos = intersection_positions(packet.channels, channel_filter)
        
        if channel_pos is None or len(channel_pos) == 0 :
            logger.debug(f"没有指定分区{name}的通道，跳过")
            pass
        
        # 分区数据包写入
        if name not in self._edf_handler.keys():
            edf_handler = RscEDFHandler(self.sample_rate,  self.digital_max , self.digital_min, self.resolution)  
            edf_handler.set_device_type(self._device_type)
            edf_handler.set_device_no(self._device_no)
            edf_handler.set_storage_path(self._storage_path)
            edf_handler.set_file_prefix(f'{self._file_prefix}_{name}' if self._file_prefix else name)
            logger.info(f"开始写入分区{name}的数据到文件")
            self._edf_handler[name] = edf_handler
        
        # 保留本分区的通道和数据
        channels = [packet.channels[p] for p in channel_pos]
        eeg = [packet.eeg[p] for p in channel_pos]
        
        # 新建数据包实例
        data = RscPacket()
        data.time_stamp = packet.time_stamp
        data.pkg_id = packet.pkg_id
        data.channels = channels
        data.origin_sample_rate = packet.origin_sample_rate
        data.sample_rate = packet.sample_rate
        data.sample_num = packet.sample_num
        data.resolution = packet.resolution
        data.trigger = packet.trigger
        data.eeg = eeg
        
        self._edf_handler[name].write(data)
    
    # trigger标记
    # desc: 标记内容
    # cur_time: 设备时间时间戳，非设备发出的trigger不要设置
    def trigger(self, desc, cur_time=None):
        # trigger现在（20250702）多个分区共享， 分发到所有分区文件中标记
        for k in self._edf_handler.keys():
            self._edf_handler[k].trigger(desc, cur_time) 
