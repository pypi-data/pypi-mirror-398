from multiprocessing import Queue, Process
from typing import Any, Dict, Literal
from threading import Thread
from loguru import logger
from time import time_ns, sleep

from qlsdk.core import *
from qlsdk.core.device import BaseDevice
from qlsdk.persist import RscEDFHandler

class QLDevice(BaseDevice):
    def __init__(self, socket):
        self.socket = socket
        
        # 设备信息
        self.device_id = None
        self.device_name = None
        self.device_type = None
        self.software_version = None
        self.hardware_version = None
        self.connect_time = None
        self.current_time = None
        # mV
        self.voltage = None
        # %
        self.battery_remain = None
        # %
        self.battery_total = None
        # persist
        self._recording = False
        self._storage_path = None
        self._file_prefix = None
        
        # 可设置参数
        # 采集：采样量程、采样率、采样通道
        # 刺激：刺激电流、刺激频率、刺激时间、刺激通道
        # 采样量程（mV）：188、375、563、750、1125、2250、4500
        self._sample_range:Literal[188, 375, 563, 750, 1125, 2250, 4500] = 188        
        # 采样率（Hz）：250、500、1000、2000、4000、8000、16000、32000
        self._sample_rate:Literal[250, 500, 1000, 2000, 4000, 8000, 16000, 32000] = 500
        self._physical_max = 188000
        self._physical_min = -188000
        self._digital_max = 8388607
        self._digital_min = -8388608
        self._physical_range = 376000
        self._digital_range = 16777215
        self._acq_channels = None
        self._acq_param = {
            "sample_range": 188,
            "sample_rate": 500,
            "channels": [],
        }
        
        self._stim_param = {
            "stim_type": 0,                 # 刺激类型：0-所有通道参数相同, 1: 通道参数不同
            "channels": [],
            "param": [{
                    "channel_id": 0,        #通道号 从0开始                          -- 必填
                    "waveform": 3,          #波形类型：0-直流，1-交流 2-方波 3-脉冲   -- 必填
                    "current": 1,           #电流强度(mA)                            -- 必填
                    "duration": 30,         #平稳阶段持续时间(s)                      -- 必填
                    "ramp_up": 5,           #上升时间(s) 默认0
                    "ramp_down": 5,         #下降时间(s) 默认0
                    "frequency": 500,       #频率(Hz) -- 非直流必填
                    "phase_position": 0,    #相位 -- 默认0
                    "duration_delay": "0",  #延迟启动时间(s) -- 默认0
                    "pulse_width": 0,       #脉冲宽度(us) -- 仅脉冲类型电流有效， 默认100us
                },
                {
                    "channel_id": 1,        #通道号 从0开始                          -- 必填
                    "waveform": 3,          #波形类型：0-直流，1-交流 2-方波 3-脉冲   -- 必填
                    "current": 1,           #电流强度(mA)                            -- 必填
                    "duration": 30,         #平稳阶段持续时间(s)                      -- 必填
                    "ramp_up": 5,           #上升时间(s) 默认0
                    "ramp_down": 5,         #下降时间(s) 默认0
                    "frequency": 500,       #频率(Hz) -- 非直流必填
                    "phase_position": 0,    #相位 -- 默认0
                    "duration_delay": "0",  #延迟启动时间(s) -- 默认0
                    "pulse_width": 0,       #脉冲宽度(us) -- 仅脉冲类型电流有效， 默认100us
                }
            ]
        }
        
        self.stim_paradigm = None
                      
        signal_info = {
            "param" : None,
            "start_time" : None,
            "finished_time" : None,
            "packet_total" : None,
            "last_packet_time" : None,
            "state" : 0
        }
        stim_info = {
            
        }
        Impedance_info = {
            
        }
        # 信号采集状态
        # 信号数据包总数（一个信号采集周期内）
        # 信号采集参数
        # 电刺激状态
        # 电刺激开始时间（最近一次）
        # 电刺激结束时间（最近一次）
        # 电刺激参数
        # 启动数据解析线程
        # 数据存储状态
        # 存储目录
        
        # 
        self.__signal_consumer: Dict[str, Queue[Any]]={}
        self.__impedance_consumer: Dict[str, Queue[Any]]={}
        
        # EDF文件处理器
        self._edf_handler = None       
        self.storage_enable = True 
        
        self._parser = DeviceParser(self)
        self._parser.start()
        
        # 启动数据接收线程
        self._accept = Thread(target=self.accept)
        self._accept.daemon = True
        self._accept.start()
        
    def init_edf_handler(self):
        self._edf_handler = RscEDFHandler(self.sample_rate,  self._physical_max , self._physical_min, self.resolution)  
        self._edf_handler.set_device_type(self.device_type)
        self._edf_handler.set_device_no(self.device_name)
        self._edf_handler.set_storage_path(self._storage_path)
        self._edf_handler.set_file_prefix(self._file_prefix)
        
    # eeg数字值转物理值
    def eeg2phy(self, digital:int):
        # 向量化计算（自动支持广播）
        return ((digital - self._digital_min) / self._digital_range) * self._physical_range + self._physical_min
    
    @property
    def edf_handler(self):
        if not self.storage_enable:
            return None
        
        if self._edf_handler is None:
            self.init_edf_handler() 
            
        return self._edf_handler  
    
    # 采集通道列表， 从1开始
    @property
    def acq_channels(self):
        if self._acq_channels is None:
            self._acq_channels = [i for i in range(1, 63)]
        return self._acq_channels
    
    # 量程范围
    @property
    def sample_range(self):
        
        return self._sample_range if self._sample_range else 188
    @property
    def sample_rate(self):
        return self._sample_rate if self._sample_rate else 500
    
    @property
    def resolution(self):
        return 24
    
    @property
    def signal_consumers(self):
        return self.__signal_consumer
    
    @property
    def impedance_consumers(self):
        return self.__impedance_consumer
    
    # 设置记录文件路径
    def set_storage_path(self, path):
        self._storage_path = path
       
    # 设置记录文件名称前缀 
    def set_file_prefix(self, prefix):
        self._file_prefix = prefix
        
    def accept(self):
        while True:
            data = self.socket.recv(4096*1024)
            if not data:
                logger.warning(f"设备{self.device_name}连接结束")
                break
            
            self._parser.append(data)
            
            
    def send(self, data):
        self.socket.sendall(data)
        
    def add_param(self, key:str, val:str):
        pass
    
    # 设置刺激参数
    def set_stim_param(self, param):
        self.stim_paradigm = param
    
    # 设置采集参数
    def set_acq_param(self, channels, sample_rate:Literal[250, 500, 1000, 2000, 4000, 8000, 16000, 32000] = 500, sample_range:Literal[188, 375, 563, 750, 1125, 2250, 4500] = 188):
        self._acq_param["channels"] = channels 
        self._acq_param["sample_rate"] = sample_rate
        self._acq_param["sample_range"] = sample_range
        self._acq_channels = channels
        self._sample_rate = sample_rate
        self._sample_range = sample_range
        # 根据量程更新信号物理值范围
        self._physical_max = self._sample_range * 1000
        self._physical_min = -self._sample_range * 1000
        self._physical_range = self._physical_max - self._physical_min
    
    # 通用配置-TODO
    def set_config(self, key:str, val: str):
        pass      
        
    def start_impedance(self):
        logger.info("启动阻抗测量")  
        msg = StartImpedanceCommand.build(self).pack()
        logger.debug(f"start_impedance message is {msg.hex()}")
        self.socket.sendall(msg)
    
    def stop_impedance(self):
        logger.info("停止阻抗测量")  
        msg = StopImpedanceCommand.build(self).pack()
        logger.debug(f"stop_impedance message is {msg.hex()}")
        self.socket.sendall(msg)
    
    def start_stimulation(self):
        if self.stim_paradigm is None:
            logger.warning("刺激参数未设置，请先设置刺激参数")
            return
        logger.info("启动电刺激")  
        msg = StartStimulationCommand.build(self).pack()
        logger.debug(f"start_stimulation message is {msg.hex()}")
        self.socket.sendall(msg)
        t = Thread(target=self._stop_stimulation_trigger, args=(self.stim_paradigm.duration,))
        t.start()
        
    def _stop_stimulation_trigger(self, duration):
        delay = duration
        while delay > 0:
            sleep(1)
            delay -= 1
        logger.info(f"_stop_stimulation_trigger duration: {duration}")
        if self._edf_handler:
            self._edf_handler.trigger("stimulation should be stopped")
        else:
            logger.warning("trigger fail for 'stop stim'. no recording file to write")
        
    def stop_stimulation(self):
        logger.info("停止电刺激")  
        msg = StopStimulationCommand.build().pack()
        logger.debug(f"stop_stimulation message is {msg.hex()}")
        self.socket.sendall(msg)
        
    # 启动采集
    def start_acquisition(self, recording = True):
        logger.info("启动信号采集")  
        self._recording = recording
        # 设置数据采集参数
        param_bytes = SetAcquisitionParamCommand.build(self).pack()
        # 启动数据采集
        start_bytes = StartAcquisitionCommand.build(self).pack()
        msg = param_bytes + start_bytes
        logger.debug(f"start_acquisition message is {msg.hex()}")
        self.socket.sendall(msg)
        
    # 停止采集
    def stop_acquisition(self):
        logger.info("停止信号采集")  
        msg = StopAcquisitionCommand.build(self).pack()
        logger.debug(f"stop_acquisition message is {msg.hex()}")
        self.socket.sendall(msg)
        if self._edf_handler:
            # 发送结束标识
            self.edf_handler.write(None)
        
    # 订阅实时数据
    def subscribe(self, topic:str=None, q : Queue=None, type : Literal["signal","impedance"]="signal"):  
            
        # 数据队列
        if q is None:
            q = Queue(maxsize=1000)
            
        # 队列名称     
        if topic is None:
            topic = f"{type}_{time_ns()}"
        
        # 订阅生理电信号数据
        if type == "signal":
            # topic唯一，用来区分不同的订阅队列（下同）
            if topic in list(self.__signal_consumer.keys()):
                logger.warning(f"exists {type} subscribe of {topic}")
            else:
                self.__signal_consumer[topic] = q
            
        # 订阅阻抗数据
        if type == "impedance":
            if topic in list(self.__signal_consumer.keys()):
                logger.warning(f"exists {type} subscribe of {topic}")
            else:
                self.__impedance_consumer[topic] = q
            
        return topic, q
    
    def trigger(self, desc):
        if self._edf_handler:
            self.edf_handler.trigger(desc)
        else:
            logger.warning("no edf handler, no place to recording trigger")
        
    def __str__(self):
        return f''' 
            Device: 
                Name: {self.device_name}, 
                Type: {hex(self.device_type) if self.device_type else None}, 
                ID: {hex(self.device_id) if self.device_id else None}, 
                Software: {self.software_version}, 
                Hardware: {self.hardware_version}, 
                Connect Time: {self.connect_time},
                Current Time: {self.current_time},
                Voltage: {str(self.voltage) + "mV" if self.voltage else None},
                Battery Remain: {str(self.battery_remain)+ "%" if self.battery_remain else None},
                Battery Total: {str(self.battery_total) + "%" if self.battery_total else None}
            '''

    def __repr__(self):
        return f''' 
            Device: 
                Name: {self.device_name}, 
                Type: {hex(self.device_type)}, 
                ID: {hex(self.device_id)}, 
                Software: {self.software_version}, 
                Hardware: {self.hardware_version}, 
                Connect Time: {self.connect_time},
                Current Time: {self.current_time},
                Voltage: {self.voltage}mV,
                Battery Remain: {self.battery_remain}%,
                Battery Total: {self.battery_total}%
            '''

    def __eq__(self, other):
        return self.device_name == other.device_name and self.device_type == other.device_type and self.device_id == other.device_id

    def __hash__(self):
        return hash((self.device_name, self.device_type, self.device_id))    
    
class RSC64RS(QLDevice):
    def __init__(self, socket):
        super().__init__(socket)
        
        
class LJS1(QLDevice):
    def __init__(self, socket):
        super().__init__(socket)
        
        
class RSC64R(QLDevice):
    def __init__(self, socket):
        super().__init__(socket)
        
        
class ARSKindling(QLDevice):
    def __init__(self, socket):
        super().__init__(socket)

class DeviceParser(object):
    def __init__(self, device : QLDevice):
        # 待解析的数据来源于该设备
        self.device = device    
        self.running = False
        
        self.cache = b''
        
    def append(self, buffer):
        self.cache += buffer
        logger.debug(f"已缓存的数据长度: {len(self.cache)}")
        
        # if not self.running:
        #     self.start()
        
    def __parser__(self):
        logger.info("数据解析开始")
        while self.running:
            if len(self.cache) < 14:
                continue
            if self.cache[0] != 0x5A or self.cache[1] != 0xA5:
                self.cache = self.cache[1:]
                continue
            pkg_len = int.from_bytes(self.cache[8:12], 'little')
            logger.trace(f" cache len: {len(self.cache)}, pkg_len len: {len(self.cache)}")
            # 一次取整包数据
            if len(self.cache) < pkg_len:
                continue
            pkg = self.cache[:pkg_len]
            self.cache = self.cache[pkg_len:]
            self.unpack(pkg)
    
    def unpack(self, packet):
        TCPMessage.parse(packet, self.device)
        # logger.debug(self.device)
        # logger.debug(f'packet len: {len(packet)}, {packet.hex()}')
            
    def start(self):
        self.running = True
        parser = Thread(target=self.__parser__,)
        parser.daemon = True
        parser.start()
        

    
class TCPMessage(object):    
    # 消息头
    HEADER_PREFIX = b'\x5A\xA5'
    # 消息头总长度 2(prefix) +1(pkgType) +1(deviceType) +4(deviceId) +4(len) +2(cmd)
    HEADER_LEN = 14  
    # 消息指令码位置
    CMD_POS = 12
    
    @staticmethod
    def parse(data: bytes, device : QLDevice) -> 'DeviceCommand':
        # 数据包校验
        TCPMessage._validate_packet(data)
        # 提取指令码
        cmd_code = int.from_bytes(data[TCPMessage.CMD_POS:TCPMessage.CMD_POS+2], 'little')
        cmd_class = CommandFactory.create_command(cmd_code)
        logger.debug(f"收到指令：{cmd_class.cmd_desc}[{hex(cmd_code)}]")
        instance = cmd_class(device)
        start = time_ns()
        logger.debug(f"开始解析: {start}")
        instance.parse_body(data[TCPMessage.HEADER_LEN:-2])
        logger.debug(f"解析完成:{time_ns()}, 解析耗时：{time_ns() - start}ns")
        return instance

    @staticmethod
    def _validate_packet(data: bytes):
        """Perform full packet validation"""
        if len(data) < TCPMessage.HEADER_LEN + 2:  # Header + min body + checksum
            raise ValueError("Packet too short")
        
        if data[0:2] != TCPMessage.HEADER_PREFIX:
            raise ValueError("Invalid header prefix")
        
        expected_len = int.from_bytes(data[8:12], 'little')
        if len(data) != expected_len:
            raise ValueError(f"Length mismatch: {len(data)} vs {expected_len}")
        
        # logger.trace(f"checksum: {int.from_bytes(data[-2:], 'little')}")
        # checksum = crc16(data[:-2])
        # logger.trace(f"checksum recv: {checksum}")
        
        
        
class DataPacket(object):
    def __init__(self, device: QLDevice):
        self.device = device
        self.header = None
        self.data = None
        
    def parse_body(self, body: bytes):
        raise NotImplementedError("Subclasses should implement this method")
