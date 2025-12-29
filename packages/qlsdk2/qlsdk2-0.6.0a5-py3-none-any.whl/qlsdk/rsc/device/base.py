from multiprocessing import Queue
from threading import Thread
from time import sleep, time_ns
from typing import Any, Dict, Literal

from loguru import logger
import numpy as np
from qlsdk.core.entity import RscPacket, ImpedancePacket
from qlsdk.core.utils import to_bytes
from qlsdk.rsc.interface import IDevice, IParser
from qlsdk.rsc.command import StartImpedanceCommand, StopImpedanceCommand, StartStimulationCommand, StopStimulationCommand, SetAcquisitionParamCommand, StartAcquisitionCommand, StopAcquisitionCommand
from qlsdk.rsc.paradigm import StimulationParadigm
from qlsdk.rsc.parser.base import TcpMessageParser

class QLBaseDevice(IDevice):
    def __init__(self, socket):
        self.socket = socket
        
        # 启动数据解析线程
        self._parser: IParser = None
        
        # 用在edf/bdf文件写入中，不建议使用
        self._record_duration = None    
        
        # 设备信息
        self.device_id = None
        self.device_name = None
        self._device_type = None
        self._device_no = None
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
        self._physical_max = self._sample_range * 1000  # 物理最大值（uV）
        self._physical_min = -self._sample_range * 1000  # 物理最小值（uV）
        self._digital_max = 8388607
        self._digital_min = -8388608
        self._physical_range = self._physical_max - self._physical_min
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
        
        self.stim_paradigm: StimulationParadigm = None
                      
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
        self._signal_consumer: Dict[str, Queue[Any]]={}
        self._impedance_consumer: Dict[str, Queue[Any]]={}
        
        # EDF文件处理器
        self._edf_handler = None       
        self.storage_enable = True 
        self._listening = False
        # self.ready()
        
    def parser(self) -> IParser:
        return self._parser
    
    def set_record_duration(self, record_duration: float):
        self._record_duration = record_duration      
    
    # 数据包处理
    def produce(self, body: bytes, type:Literal['signal', 'impedance']="signal"):
        if body is None: return      
        
        if type == "signal":
            self._produce_signal(body)
        elif type == "impedance":
            self._produce_impedance(body)       
        
    def _produce_impedance(self, body: bytes):
        packet = ImpedancePacket.transfer(body)
        # 分发阻抗数据包给订阅者
        if len(self._impedance_consumer) > 0:
            for topic, q in self._impedance_consumer.items():
                try:
                    q.put(packet, timeout=1)
                except Exception as e:
                    logger.error(f"impedance data put to queue exception: {str(e)}")
    
    def _produce_signal(self, body: bytes):        
        
        # 处理信号数据
        data = self._signal_wrapper(body)   
        # logger.debug("pkg_id: {}, eeg len: {}".format(data.pkg_id, len(data.eeg)))
        # 
        trigger_positions = [index for index, value in enumerate(data.trigger) if value != 0]
        if len(trigger_positions) > 0:
            # logger.debug(f"Trigger触发点位置: {trigger_positions}, 触发点时间戳: {[data.time_stamp + int(pos * 1000 / data.sample_rate) for pos in trigger_positions]}")
            for pos in trigger_positions:
                self.trigger(data.trigger[pos])
        # 存储
        if self.storage_enable:
            self._write_signal(data)
                        
        if len(self.signal_consumers) > 0 :
            logger.trace(f"dg eeg: {data.eeg}")
            # 信号数字值转物理值
            data.eeg = self.eeg2phy(np.array(data.eeg))
            logger.trace(f"ph eeg: {data.eeg}")
            
            # 发送数据包到订阅者
            for q in list(self.signal_consumers.values()):
                # 队列满了就丢弃最早的数据
                if q.full(): 
                    q.get()
                    
                q.put(data)        
                
    # 信号数据转换
    def _signal_wrapper(self, body: bytes):
        return RscPacket().transfer(body)
                
    def _write_signal(self, data: RscPacket):
        # 文件写入到edf
        if self._edf_handler is None:
            logger.debug("Initializing EDF handler for data storage")
            self.init_edf_handler()
        
        if self._edf_handler:  
            self._edf_handler.write(data)
        
    def start_listening(self):        
        
        try:
            # 启动消息解析器
            self.start_message_parser()
            
            # 启动消息监听器
            self.start_message_listening()
        except Exception as e:
            logger.error(f"设备{self.device_no}准备失败: {str(e)}")
            return False
        
        return True
    
    def stop_listening(self):
        logger.trace(f"设备{self.device_no}停止socket监听")
        self._listening = False        
        self._parser.stop()
     
    def read_msg(self, size: int) -> bytes:
        try:
            self.socket.settimeout(2.0)
            return self.socket.recv(size)
        except Exception as e:
            logger.error(f"read_msg exception: {str(e)}")
            raise ValueError("read_msg exception") from e
      
    @classmethod
    def from_parent(cls, parent:IDevice) -> IDevice:
        rlt = cls(parent.socket)
        rlt.device_id = parent.device_id
        rlt._device_no = parent.device_no
        return rlt
         
    @property
    def device_type(self) -> int:
        return self._device_type
    
    def start_message_parser(self) -> None:
        self._parser = TcpMessageParser(self)
        self._parser.start()
        logger.debug("RSC消息解析器已启动")
    
    def start_message_listening(self) -> None:
        def _accept():
            while self._listening:
                try:
                    # 缓冲区4M
                    data = self.socket.recv(4096*1024)
                    if not data:
                        logger.warning(f"设备[{self.device_name}]连接结束")
                        break
                    self._parser.append(data)
                except Exception as e:
                    logger.debug(f"设备[{self.device_name}]接收数据异常: {str(e)}")
                    break
    
        # 启动数据接收线程
        self._listening = True
        message_accept = Thread(target=_accept, daemon=True)
        message_accept.start()
        logger.debug(f"socket消息监听已启动")
        
    def set_device_type(self, type: int):
        self._device_type = type
        
    @property
    def device_no(self) -> int:
        return self._device_no
    
    def set_device_no(self, value: int):
        self._device_no = value
        
    @property
    def physical_max(self) -> int:
        return self._physical_max
    
    @property
    def physical_min(self) -> int:
        return self._physical_min
    
    @property
    def physical_range(self) -> int:
        return self._physical_range
    
    @property
    def digital_max(self) -> int:
        return self._digital_max
    
    @property
    def digital_min(self) -> int:
        return self._digital_min    
    
    @property
    def digital_range(self) -> int:
        return self._digital_range
    
    def init_edf_handler(self):
        logger.warning("init_edf_handler not implemented in base class, should be overridden in subclass")
        pass
        
    # eeg数字值转物理值
    def eeg2phy(self, digital:int):
        # 向量化计算（自动支持广播）
        return ((digital - self.digital_min) / self.digital_range) * self.physical_range + self.physical_min
    
    @property
    def edf_handler(self):
        if not self.storage_enable:
            logger.warning("EDF storage is disabled, no edf handler available")
            return None
        
        if self._edf_handler is None:
            self.init_edf_handler() 
            
        return self._edf_handler  
    
    @property
    def acq_channels(self):
        if self._acq_channels is None:
            self._acq_channels = [i for i in range(1, 63)]
        return self._acq_channels
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
    def sample_num(self) -> int:
        return 10
    @property
    def signal_consumers(self):
        return self._signal_consumer
    
    @property
    def impedance_consumers(self):
        return self._impedance_consumer
    
    # 设置记录文件路径
    def set_storage_path(self, path):
        self._storage_path = path
       
    # 设置记录文件名称前缀 
    def set_file_prefix(self, prefix):
        self._file_prefix = prefix
       
    # socket发送数据    
    def send(self, data):
        self.socket.sendall(data)
    
    # 设置刺激参数
    def set_stim_param(self, param):
        self.stim_paradigm = param
    
    # 设置采集参数
    def set_acq_param(self, channels, sample_rate:Literal[188, 375, 563, 750, 1125, 2250, 4500] = 500, sample_range:Literal[250, 500, 1000, 2000, 4000, 8000, 16000, 32000] = 188):
        self._acq_param["channels"] = channels 
        self._acq_param["sample_rate"] = sample_rate
        self._acq_param["sample_range"] = sample_range
        self._acq_channels = channels
        self._sample_rate = sample_rate
        self._sample_range = sample_range
    
    # 通用配置-TODO
    def set_config(self, key:str, val: str):
        pass      
        
    def start_impedance(self):
        logger.info(f"[设备-{self.device_no}]启动阻抗测量")  
        msg = StartImpedanceCommand.build(self).pack()
        logger.trace(f"start_impedance message is {msg.hex()}")
        self.socket.sendall(msg)
    
    def stop_impedance(self):
        logger.info(f"[设备{self.device_no}]停止阻抗测量")  
        msg = StopImpedanceCommand.build(self).pack()
        logger.trace(f"stop_impedance message is {msg.hex()}")
        self.socket.sendall(msg)
    
    def start_stimulation(self):
        if self.stim_paradigm is None:
            logger.warning("刺激参数未设置，请先设置刺激参数")
            return
        logger.info(f"[设备-{self.device_no}]启动电刺激")  
        msg = StartStimulationCommand.build(self).pack()
        logger.trace(f"start_stimulation message is {msg.hex()}")
        self.socket.sendall(msg)
        t = Thread(target=self._stop_stimulation_trigger, args=(self.stim_paradigm.duration,), daemon=True)
        t.start()
        
    def get_stim_param(self) -> bytes:
        return self.stim_paradigm.to_bytes()
        
    def _stop_stimulation_trigger(self, duration):
        delay = duration
        while delay > 0:
            sleep(1)
            delay -= 1
        logger.debug(f"_stop_stimulation_trigger duration: {duration}")
        if self._edf_handler:
            self._edf_handler.trigger("stimulation should be stopped")
        else:
            logger.warning("stop stim trigger fail. no edf writer alive")
        
    def stop_stimulation(self):
        logger.info(f"[设备-{self.device_no}]停止电刺激")  
        msg = StopStimulationCommand.pack()
        logger.trace(f"stop_stimulation message is {msg.hex()}")
        self.socket.sendall(msg)
        
    # 启动采集
    def start_acquisition(self, recording = True):
        logger.info(f"[设备-{self.device_no}]启动信号采集")  
        self._recording = recording
        # 初始化EDF处理器
        self.init_edf_handler()
        # 设置数据采集参数
        param_bytes = SetAcquisitionParamCommand.build(self).pack()
        # 启动数据采集
        start_bytes = StartAcquisitionCommand.build(self).pack()
        msg = param_bytes + start_bytes
        logger.trace(f"start_acquisition message is {msg.hex()}")
        self.socket.sendall(msg)
        
    # 停止采集
    def stop_acquisition(self):
        logger.info(f"[设备-{self.device_no}]停止信号采集")  
        msg = StopAcquisitionCommand.build(self).pack()
        logger.trace(f"stop_acquisition message is {msg.hex()}")
        self.socket.sendall(msg)
        if self._edf_handler:
            # 发送结束标识
            self.edf_handler.write(None)
        
    '''
        订阅数据
        topic: 订阅主题
        q: 数据队列
        type: 数据类型，signal-信号数据，impedance-阻抗数据
    '''
    def subscribe(self, topic:str=None, q : Queue=None, type : Literal["signal","impedance"]="signal"):  
            
        # 队列名称     
        if topic is None:
            topic = f"{self.device_no}_{type}_{time_ns()}"
            
        logger.debug(f"[设备-{self.device_no}]订阅数据流： {topic}, type: {type}")    
            
        # 数据队列
        if q is None:
            q = Queue(maxsize=1024 * 1024)
        
        # 订阅生理电信号数据
        if type == "signal":
            # topic唯一，用来区分不同的订阅队列（下同）
            if topic in list(self._signal_consumer.keys()):
                logger.warning(f"已存在主题[{topic}]的信号数据订阅！")
            else:
                self._signal_consumer[topic] = q
            
        # 订阅阻抗数据
        if type == "impedance":
            if topic in list(self._impedance_consumer.keys()):
                logger.warning(f"已存在主题[{topic}]的阻抗数据订阅！")
            else:
                self._impedance_consumer[topic] = q
            
        return topic, q
    
    def trigger(self, desc):
        if self._edf_handler:
            self.edf_handler.trigger(desc)
        else:
            logger.warning("没有开启文件记录时，无法记录trigger信息")
        
    def gen_set_acquirement_param(self) -> bytes:
        
        body = to_bytes(self.acq_channels) 
        body += self.sample_range.to_bytes(4, byteorder='little')
        body += self.sample_rate.to_bytes(4, byteorder='little')
        body += self.sample_num.to_bytes(4, byteorder='little')
        body += self.resolution.to_bytes(1, byteorder='little')
        body += bytes.fromhex('00')     
        
        return body
    
    def disconnect(self):
        logger.info(f"[断开设备-{self.device_no}]的连接...")  
        self._listening = False
        try:
            sleep(0.1)
            self.socket.shutdown(2)
            self.socket.close()
            logger.info(f"[设备-{self.device_no}]设备连接已断开")  
        except Exception as e:
            logger.error(f"断开设备连接异常: {str(e)}")
         
        # 关闭解析器
        self._parser.stop()   
    
    def __str__(self):
        return f''' 
            Device: 
                Name: {self.device_name}, 
                Type: {hex(self.device_type) if self.device_type else None}, 
                ID: {self.device_no if self.device_no else None}, 
                Software: {self.software_version}, 
                Hardware: {self.hardware_version}, 
                Connect Time: {self.connect_time},
                Current Time: {self.current_time},
                Voltage: {str(self.voltage) + "mV" if self.voltage else None},
                Battery Remain: {str(self.battery_remain)+ "%" if self.battery_remain else None},
                Battery Total: {str(self.battery_total) + "%" if self.battery_total else None}
            '''

    def __eq__(self, other:IDevice):
        return self.device_type == other.device_type and self.device_no == other.device_no

    def __hash__(self):
        return hash((self.device_type, self.device_no))    