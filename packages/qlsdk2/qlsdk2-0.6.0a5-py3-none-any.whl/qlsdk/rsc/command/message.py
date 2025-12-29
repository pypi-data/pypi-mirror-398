import abc
import numpy as np
from time import time_ns
from typing import Dict, Type
from loguru import logger


from qlsdk.core.crc import crc16
from qlsdk.core.device import BaseDevice, 
from qlsdk.core.entity import RscPacket, ImpedancePacket
from qlsdk.core.utils import to_channels, to_bytes
from qlsdk.rsc.interface import IDevice, IParser
from qlsdk.rsc.device import DeviceFactory

class DeviceCommand(abc.ABC):
    # 消息头
    HEADER_PREFIX = b'\x5A\xA5'
    # 消息头总长度 2(prefix) +1(pkgType) +1(deviceType) +4(deviceId) +4(len) +2(cmd)
    HEADER_LEN = 14  
    # 消息指令码位置
    CMD_POS = 12
    
    def __init__(self, device: BaseDevice):
        self.device = device
        
    @classmethod
    def build(cls, device) :
        return cls(device)
    
    @property
    @abc.abstractmethod
    def cmd_code(self) -> int:
        pass
    @property
    @abc.abstractmethod
    def cmd_desc(self) -> str:
        pass
    
    @staticmethod
    def checksum(data: bytes) -> bytes:
        return crc16(data).to_bytes(2, 'little')

    def pack(self, body=b'') -> bytes:
        # header+body+checksum
        body = self.pack_body()
        header = self.pack_header(len(body))
        payload = header + body
        return payload + DeviceCommand.checksum(payload)
    def pack_body(self) -> bytes:
        """构建消息体"""
        return b''
    def pack_header(self, body_len: int) -> bytes:
        device_id = int(self.device.device_id) if self.device and self.device.device_id else 0
        device_type = int(self.device.device_type) if self.device and self.device.device_type else 0
        
        """构建消息头"""
        return (
            DeviceCommand.HEADER_PREFIX
            + int(2).to_bytes(1, 'little')     # pkgType  
            + device_type.to_bytes(1, 'little')
            + device_id.to_bytes(4, 'little')
            + (DeviceCommand.HEADER_LEN + body_len + 2).to_bytes(4, 'little')  # +1 for checksum
            + self.cmd_code.to_bytes(2, 'little')
        )
    
    def unpack(self, payload: bytes) -> bytes:
        """解析消息体"""
        # 解析消息体
        body = payload[self.HEADER_LEN:-2]   
    
    def parse_body(self, body: bytes):
        time = int.from_bytes(body[0:8], 'little')
        # result - 1B
        result = body[8]
        logger.info(f"[{time}]{self.cmd_desc}{'成功' if result == 0 else '失败'}")
        
    

class CommandFactory:
    """Registry for command implementations"""
    _commands: Dict[int, Type[DeviceCommand]] = {}
    
    @classmethod
    def register_command(cls, code: int, command: Type[DeviceCommand]):
        cls._commands[code] = command
    
    @classmethod
    def create_command(cls, code: int) -> Type[DeviceCommand]:
        logger.trace(f"Creating command for code: {hex(code)}")
        if code not in cls._commands:
            logger.warning(f"不支持的设备指令: {hex(code)}")
            return cls._commands[DefaultCommand.cmd_code]
        return cls._commands[code]

# =============================================================================
class DefaultCommand(DeviceCommand):    
    cmd_code = 0x00   
    cmd_desc = "未定义"
        
    def parse_body(self, body: bytes):
        # Response parsing example: 2 bytes version + 4 bytes serial
        logger.info(f"Received body len: {len(body)}")
    
class GetDeviceInfoCommand(DeviceCommand):
    cmd_code = 0x17
    cmd_desc = "设备信息"
    
    def parse_body(self, body: bytes):
        # time - 8B
        self.device.connect_time = int.from_bytes(body[0:8], 'little')
        self.device.current_time = self.device.connect_time
        # result - 1B
        result = body[8]
        # deviceId - 4B
        self.device.device_id = int.from_bytes(body[9:13], 'big')
        # deviceType - 4B
        self.device.device_type = int.from_bytes(body[13:17], 'little')
        # softVersion - 4B
        self.device.software_version = body[17:21].hex()
        # hardVersion - 4B
        self.device.hardware_version = body[21:25].hex()
        # deviceName - 16B
        self.device.device_name = body[25:41].decode('utf-8').rstrip('\x00')
        # flag - 4B
        flag = int.from_bytes(body[41:45], 'little')
        logger.debug(f"Received device info: {result}, {flag}, {self.device}")
        
        # 创建设备对象
        device = Dev
        

# 握手
class HandshakeCommand(DeviceCommand):
    cmd_code = 0x01
    cmd_desc = "握手"
    
    def parse_body(self, body: bytes):
        logger.info(f"Received handshake response: {body.hex()}")

# 查询电量
class QueryBatteryCommand(DeviceCommand):
    cmd_code = 0x16
    cmd_desc = "电量信息"
    def parse_body(self, body: bytes):
        # time - 8b
        self.device.current_time = int.from_bytes(body[0:8], 'little')
        # result - 1b
        result = body[8]
        # 更新设备信息
        if result == 0:
            # voltage - 2b mV
            self.device.voltage = int.from_bytes(body[9:11], 'little')
            # soc - 1b
            self.device.battery_remain = body[11]
            # soh - 1b
            self.device.battery_total = body[12]
            # state - 1b
            # state = body[13]
            logger.debug(f"电量更新: {self.device}")
        else:
            logger.warning(f"QueryBatteryCommand message received but result is failed.")

# 设置采集参数
class SetAcquisitionParamCommand(DeviceCommand):
    cmd_code = 0x451
    cmd_desc = "设置信号采集参数"
    
    def pack_body(self):
        body = to_bytes(self.device.acq_channels) 
        body += self.device.sample_range.to_bytes(4, byteorder='little')
        body += self.device.sample_rate.to_bytes(4, byteorder='little')
        body += self.device.sample_num.to_bytes(4, byteorder='little')
        body += self.device.resolution.to_bytes(1, byteorder='little')
        body += bytes.fromhex('00')        

        return body
        
# 启动采集
class StartAcquisitionCommand(DeviceCommand):
    cmd_code = 0x452
    cmd_desc = "启动信号采集"
    
    def pack_body(self):
        return bytes.fromhex('0000')

# 停止采集
class StopAcquisitionCommand(DeviceCommand):
    cmd_code = 0x453
    cmd_desc = "停止信号采集"
    
    def pack_body(self):
        return b''

        
# 设置阻抗采集参数
class SetImpedanceParamCommand(DeviceCommand):
    cmd_code = 0x411
    cmd_desc = "设置阻抗测量参数"
        
# 启动阻抗测量
class StartImpedanceCommand(DeviceCommand):
    cmd_code = 0x412
    cmd_desc = "启动阻抗测量"
    def pack_body(self):
        body = bytes.fromhex('0000')
        body += to_bytes(self.device.acq_channels)
        body += bytes.fromhex('0000000000000000') # 8字节占位符
        return body
        

# 停止阻抗测量
class StopImpedanceCommand(DeviceCommand):
    cmd_code = 0x413
    cmd_desc = "停止阻抗测量"
    
    def pack_body(self):
        return b''
            
# 启动刺激
class StartStimulationCommand(DeviceCommand):
    cmd_code = 0x48C
    cmd_desc = "启动刺激"
    def pack_body(self):
        return self.device.stim_paradigm.to_bytes()
        # return bytes.fromhex('01000000000000008813000000000000010000000000000000000140420f00640064000000803f0000010000000000000000000000000000000000000000008813000000000000')
    def parse_body(self, body: bytes):
        # time - 8B
        time = int.from_bytes(body[0:8], 'little')
        # result - 1B
        result = body[8]
        # error_channel - 8B
        # error_channel= int.from_bytes(body[9:17], 'big')
        channels = to_channels(body[9:17])
        logger.success(f"通道 {channels} 刺激开始")
        self.device.trigger(f"通道 {channels} 刺激开始")
        # error_type - 1B
        error_type = body[17]

# 停止刺激
class StopStimulationCommand(DeviceCommand):
    cmd_code = 0x488
    cmd_desc = "停止刺激"
     
# 启动刺激
class StopStimulationNotifyCommand(DeviceCommand):
    cmd_code = 0x48D
    cmd_desc = "停止刺激通知"
    def pack_body(self):
        return self.device.stim_paradigm.to_bytes()
        # return bytes.fromhex('01000000000000008813000000000000010000000000000000000140420f00640064000000803f0000010000000000000000000000000000000000000000008813000000000000')
    def parse_body(self, body: bytes):
        # time - 8B
        time = int.from_bytes(body[0:8], 'little')
        # result - 1B
        result = body[8]
        # error_channel - 8B
        # error_channel= int.from_bytes(body[9:17], 'big')
        channels = to_channels(body[9:17])
        logger.success(f"通道 {channels} 刺激结束")
        self.device.trigger(f"通道 {channels} 刺激结束", time)
        # error_type - 1B
        error_type = body[17]   
# 刺激信息
class StimulationInfoCommand(DeviceCommand):
    cmd_code = 0x48e
    cmd_desc = "刺激告警信息"
    
    def parse_body(self, body: bytes):
        time = int.from_bytes(body[0:8], 'little')
        # result - 1B
        result = body[8]
        # error_channel - 8B
        channels = to_channels(body[9:17])
        # 保留位-8B
        # error_type - 1B
        err_type = body[17]
        # 特征位-4B
        # errType  = int.from_bytes(body[25:29], 'little')
        logger.warning(f"刺激告警信息[{err_type}]，通道 {channels} 刺激驱动不足")
        

# 阻抗数据
class ImpedanceDataCommand(DeviceCommand):
    cmd_code = 0x415
    cmd_desc = "阻抗数据"
    
    def parse_body(self, body: bytes):
        logger.info(f"Received impedance data: {body.hex()}")
        packet = ImpedancePacket().transfer(body)

# 信号数据
class SignalDataCommand(DeviceCommand):
    cmd_code = 0x455
    cmd_desc = "信号数据"
    
    def unpack(self, payload):
        return super().unpack(payload)
    
    def parse_body(self, body: bytes):     
        # 解析数据包
        packet = RscPacket()
        packet.transfer(body)  
        
        # 文件写入到edf
        if self.device.edf_handler:
            self.device.edf_handler.write(packet)
                        
        if len(self.device.signal_consumers) > 0 :
            # 信号数字值转物理值
            packet.eeg = self.device.eeg2phy(np.array(packet.eeg))
            
            # 发送数据包到订阅者
            for q in list(self.device.signal_consumers.values()):
                q.put(packet)
                
            

# =============================================================================
# 指令实现类注册到指令工厂
# =============================================================================
CommandFactory.register_command(DefaultCommand.cmd_code, DefaultCommand)
CommandFactory.register_command(GetDeviceInfoCommand.cmd_code, GetDeviceInfoCommand)
CommandFactory.register_command(HandshakeCommand.cmd_code, HandshakeCommand)
CommandFactory.register_command(QueryBatteryCommand.cmd_code, QueryBatteryCommand)
CommandFactory.register_command(SetAcquisitionParamCommand.cmd_code, SetAcquisitionParamCommand)
CommandFactory.register_command(StartAcquisitionCommand.cmd_code, StartAcquisitionCommand)
CommandFactory.register_command(StopAcquisitionCommand.cmd_code, StopAcquisitionCommand)
CommandFactory.register_command(SetImpedanceParamCommand.cmd_code, SetImpedanceParamCommand)
CommandFactory.register_command(StartImpedanceCommand.cmd_code, StartImpedanceCommand)
CommandFactory.register_command(StopImpedanceCommand.cmd_code, StopImpedanceCommand)
CommandFactory.register_command(StartStimulationCommand.cmd_code, StartStimulationCommand)
CommandFactory.register_command(StimulationInfoCommand.cmd_code, StimulationInfoCommand)
CommandFactory.register_command(ImpedanceDataCommand.cmd_code, ImpedanceDataCommand)
CommandFactory.register_command(SignalDataCommand.cmd_code, SignalDataCommand)


