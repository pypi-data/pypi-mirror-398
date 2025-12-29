from datetime import datetime
from multiprocessing import Lock, Queue
from pyedflib import FILETYPE_BDFPLUS, FILETYPE_EDFPLUS, EdfWriter
from threading import Thread
from loguru import logger
import numpy as np
import os

class EdfHandler(object):
    def __init__(self, sample_frequency, physical_max, physical_min, digital_max, digital_min, resolution=16, storage_path = None):
        self.physical_max = physical_max
        self.physical_min = physical_min
        self.digital_max = digital_max
        self.digital_min = digital_min
        self.eeg_channels = None
        self.eeg_sample_rate = 500
        self.acc_channels = None
        self.acc_sample_rate = 50
        self._cache = Queue()
        self.resolution = resolution
        self.sample_frequency = sample_frequency
        # bytes per second
        self.bytes_per_second = 0
        self._edf_writer = None
        self._cache2 = tuple()
        self._recording = False
        self._edf_writer = None
        self.annotations = None
        # 每个数据块大小
        self._chunk = np.array([])
        self._Lock = Lock()
        self._duration = 0
        self._points = 0
        self._first_pkg_id = None
        self._last_pkg_id = None
        self._first_timestamp = None
        self._first_time = None
        self._end_time = None
        self._patient_code = "patient_code"
        self._patient_name = "patient_name"
        self._device_type = None
        self._total_packets = 0
        self._lost_packets = 0
        self._storage_path = storage_path
        
    @property
    def file_name(self): 
        if self._storage_path:
            try:
                os.makedirs(self._storage_path, exist_ok=True)  # 自动创建目录，存在则忽略
                return f"{self._storage_path}/{self._device_type}_{self._first_timestamp}.edf"
            except Exception as e:
                logger.error(f"创建目录[{self._storage_path}]失败: {e}")
            
        return f"{self._device_type}_{self._first_timestamp}.edf"
         
    @property
    def file_type(self):
        return FILETYPE_BDFPLUS if self.resolution == 24 else FILETYPE_EDFPLUS
    
    def set_device_type(self, device_type):
        self._device_type = device_type
        
    def set_storage_path(self, storage_path):
        self._storage_path = storage_path
        
    def set_patient_code(self, patient_code):
        self._patient_code = patient_code
        
    def set_patient_name(self, patient_name):
        self._patient_name = patient_name
    
    def append(self, data):
        if data:
            # 通道数
            if self._first_pkg_id is None:
                self.eeg_channels = data.eeg_ch_count
                self.acc_channels = data.acc_ch_count
                self._first_pkg_id = data.pkg_id
                self._first_timestamp = data.time_stamp
                self._first_time = datetime.now()
                
            if self._last_pkg_id and self._last_pkg_id != data.pkg_id - 1:  
                self._lost_packets += data.pkg_id - self._last_pkg_id - 1
                logger.warning(f"数据包丢失: {self._last_pkg_id} -> {data.pkg_id}, 丢包数: {data.pkg_id - self._last_pkg_id - 1}")
                
            self._last_pkg_id = data.pkg_id
            self._total_packets += 1
            
        # 数据
        self._cache.put(data)
        if not self._recording:
            self.start()
    
    # trigger标记
    # desc: 标记内容
    # cur_time: 设备时间时间戳，非设备发出的trigger不要设置
    def trigger(self, desc, cur_time=None):
        if self._edf_writer is None:
            logger.warning("EDF writer未初始化，无法写入trigger标记")
            return
        
        if cur_time is None:
            onset = datetime.now().timestamp() - self._first_time.timestamp()
        else:
            onset = cur_time - self._first_timestamp
            
        self._edf_writer.writeAnnotation(onset, 1, desc)
    
    
    # def trigger(self, desc):
    #     if self._edf_writer:            
    #         self._edf_writer.writeAnnotation(0, 1, desc)
    
    def start(self):
        self._recording = True
        record_thread = Thread(target=self._consumer)
        record_thread.start()
        
    def _consumer(self):
        logger.debug(f"开始消费数据 _consumer: {self._cache.qsize()}")
        while True:
            if self._recording or (not self._cache.empty()):
                try:
                    data = self._cache.get(timeout=10)
                    if data is None:
                        break
                    # 处理数据
                    self._points += len(data.eeg[0])
                    self._write_file(data.eeg, data.acc)
                except Exception as e:
                    logger.error("数据队列为空，超时(10s)结束")
                    break
            else:
                break
            
        self.close()
        
    def _write_file(self, eeg_data, acc_data):
        try:
            if self._edf_writer is None:
                self.initialize_edf()
            
            if (self._chunk.size == 0):
                self._chunk = np.asarray(eeg_data)
            else:                
                self._chunk = np.hstack((self._chunk, eeg_data))
                
            if self._chunk.size >= self.eeg_sample_rate * self.eeg_channels:                
                self._write_chunk(self._chunk[:self.sample_frequency])
                self._chunk = self._chunk[self.sample_frequency:]            
            
        except Exception as e:
            logger.error(f"写入数据异常: {str(e)}")
        
    def close(self):
        self._recording = False
        if self._edf_writer:            
            self._end_time = datetime.now().timestamp()
            self._edf_writer.writeAnnotation(0, 1, "start recording ")
            self._edf_writer.writeAnnotation(self._duration, 1, "recording end")
            self._edf_writer.close()
        
        logger.info(f"文件: {self.file_name}完成记录, 总点数: {self._points}, 总时长: {self._duration}秒 丢包数: {self._lost_packets}/{self._total_packets + self._lost_packets}")
        
    
        
    def initialize_edf(self):
        # 创建EDF+写入器
        self._edf_writer = EdfWriter(
            self.file_name,
            self.eeg_channels,
            file_type=self.file_type
        )
        
        # 设置头信息
        self._edf_writer.setPatientCode(self._patient_code)
        self._edf_writer.setPatientName(self._patient_name)
        self._edf_writer.setEquipment(self._device_type)
        self._edf_writer.setStartdatetime(datetime.now())
        
        # 配置通道参数
        signal_headers = []
        for ch in range(self.eeg_channels):
            signal_headers.append({
                "label": f'channels {ch + 1}',
                "dimension": 'uV',
                "sample_frequency": self.sample_frequency,
                "physical_min": self.physical_min,
                "physical_max": self.physical_max,
                "digital_min": self.digital_min,
                "digital_max": self.digital_max
            })
        
        self._edf_writer.setSignalHeaders(signal_headers)
    
    def _write_chunk(self, chunk):
        logger.debug(f"写入数据: {chunk}")
        # 转换数据类型为float64（pyedflib要求）
        data_float64 = chunk.astype(np.float64)
        # 写入时转置为(样本数, 通道数)格式
        self._edf_writer.writeSamples(data_float64)
        self._duration += 1

    