

from datetime import datetime
from multiprocessing import Lock, Queue
from time import time_ns
from pyedflib import FILETYPE_BDFPLUS, FILETYPE_EDFPLUS, EdfWriter
from threading import Thread
from loguru import logger
import numpy as np

EDF_FILE_TYPE = {
    "bdf": FILETYPE_BDFPLUS,
    "edf": FILETYPE_EDFPLUS
}

class EDFStreamWriter(Thread):
    def __init__(self, channels, sample_frequency, physical_max, digital_min, file_type, file_path):
        super().__init__()
        self._writer : EdfWriter = None
        self.data_queue : Queue = Queue()
        self._recording = False
        self._points = 0
        self._duration = 0
        self._buffer = None
        
        # signal info
        self._channels = channels
        self._n_channels = len(channels)
        self.sample_frequency = sample_frequency
        self.physical_max = physical_max
        self.physical_min = digital_min
        # 和位数相关，edf 16 bits/bdf  24 bits
        self.digital_max = 8388607 if file_type == EDF_FILE_TYPE['bdf'] else 32767
        self.digital_min = -8388608 if file_type == EDF_FILE_TYPE['bdf'] else -32768
        self.file_type = file_type
        self.file_path = file_path
        
        # 记录开始时间
        self.start_time = None
        
        # header info
        self.equipment = "equipment"
        self.patient_code = "patient_code"
        self.patient_name = "patient_name"
        
    def set_channels(self, channels):
        self._channels = channels
        self._n_channels = len(channels)
        
    def set_sample_rate(self, sample_rate):
        self._sample_rate = sample_rate
        
    def set_start_time(self, time):
        self.start_time = time

    def stop_recording(self):
        self._recording = False
        
    def append(self, data):
        if data:
            # 数据
            self.data_queue.put(data)
            
    def trigger(self, onset, desc):
        if self._writer:            
            self._writer.writeAnnotation(onset, 1, desc)
        else:
            logger.warning("未创建文件，无法写入Trigger标记")
        
        
    def run(self):
        logger.debug(f"启动bdf文件写入线程，写入数据到文件 {self.file_path}")
        # 记录状态
        self._recording = True
        
        #  初始化
        if self._writer is None:
            self._init_writer()
            
        while True:
            if self._recording or (not self.data_queue.empty()):
                try:
                    data = self.data_queue.get(timeout=30)
                    if data is None:
                        logger.debug("收到结束信号，停止写入数据")
                        break
                    # 处理数据
                    self._points += len(data[1])
                    logger.trace(f"已处理数据点数：{self._points}")
                    self._write_file(data)
                except Exception as e:
                    logger.error(f"异常或超时(30s)结束: {str(e)}")
                    break
            else:
                logger.debug("数据记录完成")
                break
            
        self.close()
        
    def _init_writer(self):
        
        # 创建EDF+写入器
        self._writer = EdfWriter(
            self.file_path,
            self._n_channels,
            file_type=self.file_type
        )
        
        # 设置头信息
        self._writer.setPatientCode(self.patient_code)
        self._writer.setPatientName(self.patient_name)
        self._writer.setEquipment(self.equipment)
        self._writer.setStartdatetime(self.start_time if self.start_time else datetime.now())
        
        # 配置通道参数
        signal_headers = []
        for ch in range(self._n_channels):
            signal_headers.append({
                "label": f'channels {self._channels[ch]}',
                "dimension": 'uV',
                "sample_frequency": self.sample_frequency,
                "physical_min": self.physical_min,
                "physical_max": self.physical_max,
                "digital_min": self.digital_min,
                "digital_max": self.digital_max
            })
        
        self._writer.setSignalHeaders(signal_headers)
        
    def _write_file(self, eeg_data):
        try:            
            if self._buffer is None or self._buffer.size == 0:
                self._buffer = np.asarray(eeg_data)
            else:                
                self._buffer = np.hstack((self._buffer, eeg_data))
            
            if self._buffer.shape[1] >= self.sample_frequency:      
                block = self._buffer[:, :self.sample_frequency]          
                self._write_block(block)
                self._buffer = self._buffer[:, self.sample_frequency:]      
            
        except Exception as e:
            logger.error(f"写入数据异常: {str(e)}")
        
    def close(self):
        self._recording = False
        if self._writer:            
            self._writer.writeAnnotation(0, 1, "recording start")
            self._writer.writeAnnotation(self._duration, 1, "recording end")
            self._writer.close()
        
        logger.info(f"文件: {self.file_path}完成记录, 总点数: {self._points}, 总时长: {self._duration}秒")
    
    # 写入1秒的数据
    def _write_block(self, block):
        logger.trace(f"写入数据: {block}")
        # 转换数据类型为float64
        data_float64 = block.astype(np.float64)
        # 写入时转置为(样本数, 通道数)格式
        self._writer.writeSamples(data_float64)
        self._duration += 1