from qlsdk.core.utils import to_channels
from loguru import logger

class Packet(object):
    def __init__(self):
        self.time_stamp = None
        self.pkg_id = None
        self.result = None
        self.channels = None
        
            
class RscPacket(Packet):
    def __init__(self):
        super().__init__()
        self.origin_sample_rate = None
        self.sample_rate = None
        self.sample_num = None
        self.resolution = None
        self.filter = None
        self.data_len = None
        self.trigger = None
        self.eeg = None
    
    @staticmethod
    def transfer(body: bytes) -> 'RscPacket':
        packet = RscPacket()
        packet.time_stamp = int.from_bytes(body[0:8], 'little')
        packet.result = body[8]
        packet.pkg_id = int.from_bytes(body[9: 13], 'little')
        logger.trace(f"pkg_id: {packet.pkg_id}")
        packet.channels = to_channels(body[13: 45])
        packet.origin_sample_rate = int.from_bytes(body[45: 49], 'little')
        packet.sample_rate = int.from_bytes(body[49: 53], 'little')
        packet.sample_num = int.from_bytes(body[53: 57], 'little')
        packet.resolution = int(int(body[57]) / 8)
        packet.filter = body[58]
        packet.data_len = int.from_bytes(body[59: 63], 'little')
        # 步径 相同通道的点间隔
        step = int(len(packet.channels) * packet.resolution + 4)
        b_eeg = body[63:]
        ch_num = len(packet.channels) 
        # 字节序列(4Cn{channel_size}){sample_num})
        packet.trigger = [int.from_bytes(b_eeg[j * step : j * step + 4], 'little', signed=False) for j in range(packet.sample_num)]
        
        packet.eeg = [
            [
                int.from_bytes(b_eeg[i * packet.resolution + 4 + j * step:i * packet.resolution + 4 + j * step + 3], 'big', signed=True)
                for j in range(packet.sample_num)
            ]
            for i in range(ch_num)
        ]
                
        logger.trace(packet)
        
        return packet
        
    def __str__(self):
        return f"""
            time_stamp: {self.time_stamp}
            pkg_id: {self.pkg_id}
            origin_sample_rate: {self.origin_sample_rate}
            sample_rate: {self.sample_rate}
            sample_num: {self.sample_num}
            resolution: {self.resolution}
            filter: {self.filter}
            channels: {self.channels}
            data len: {self.data_len}
            trigger: {self.trigger}
            eeg: {self.eeg}
        """
        
class ImpedancePacket(Packet):
    def __init__(self):
        super().__init__()
        self.impedance = None
        
    @staticmethod
    def transfer(body:bytes) -> 'ImpedancePacket':
        packet = ImpedancePacket()
        packet.time_stamp = int.from_bytes(body[0:8], 'little')
        # packet.result = body[8]
        packet.pkg_id = int.from_bytes(body[9: 13], 'little')
        packet.channels = to_channels(body[13: 45])
        # packet.sample_rate = int.from_bytes(body[45: 49], 'little')
        # packet.sample_len = int.from_bytes(body[49: 53], 'little')
        # packet.resolution = int(int(body[53]) / 8)
        # packet.filter = int(int(body[54]) / 8)
        # packet.wave_type = int(int(body[55]) / 8)
        # packet.wave_freq = int.from_bytes(body[56: 60], 'little')
        # packet.data_len = int.from_bytes(body[60: 64], 'little')
        b_impedance = body[64:]
        packet.impedance = [int.from_bytes(b_impedance[j * 4 : j * 4 + 4], 'little', signed=False) for j in range(len(packet.channels))]

        logger.trace(f"impedance: {packet}")
        
        return packet

    def __str__(self):
        return f"""
            time_stamp: {self.time_stamp}
            pkg_id: {self.pkg_id}
            channels: {self.channels}
            impedance: {self.impedance}
        """
        
    
class C256RSPacket(Packet):
    def __init__(self):
        super().__init__()
        self.origin_sample_rate = None
        self.sample_rate = None
        self.sample_num = None
        self.resolution = None
        self.filter = None
        self.data_len = None
        self.trigger = None
        self.eeg = None
    
    @staticmethod
    def transfer(body: bytes) -> 'RscPacket':
        packet = RscPacket()
        packet.time_stamp = int.from_bytes(body[0:8], 'little')
        packet.result = body[8]
        packet.pkg_id = int.from_bytes(body[9: 13], 'little')
        packet.channels = to_channels(body[13: 45])
        logger.trace(f"pkg_id: {packet.pkg_id}, channels: {packet.channels}")
            
        packet.origin_sample_rate = int.from_bytes(body[45: 49], 'little')
        packet.sample_rate = int.from_bytes(body[49: 53], 'little')
        packet.sample_num = int.from_bytes(body[53: 57], 'little')
        packet.resolution = int(int(body[57]) / 8)
        packet.filter = body[58]
        packet.data_len = int.from_bytes(body[59: 63], 'little')
                
        # 数据块
        b_eeg = body[63:]
        # 根据值域分割数组-代表设备的4个模块
        ranges = [(1, 64), (65, 128), (129, 192), (193, 256)]
        sub_channels = [[x for x in packet.channels if low <= x <= high] for low, high in ranges]
        # 只处理选中的模块
        sub_channels = [_ for _ in sub_channels if len(_) > 0]
        # 步径 相同通道的点间隔
        step = int(len(packet.channels) * packet.resolution + 4 * len(sub_channels))
        offset = 0
        
        # 分按子模块处理
        for channels in sub_channels:
            logger.trace(f"子数组: {channels} 长度: {len(channels)}")
            channel_size = len(channels) 
            
            # 模块没有选中通道的，跳过
            if channel_size == 0:
                continue
            
            # 只保留第一个有效模块的trigger，其他的模块是冗余信息，无实际含义
            if packet.trigger is None:
                packet.trigger = [int.from_bytes(b_eeg[j * step : j * step + 4], 'little', signed=False) for j in range(packet.sample_num)]
                logger.trace(f"trigger: {packet.trigger}")
                trigger_positions = [index for index, value in enumerate(packet.trigger) if value != 0]
                if len(trigger_positions) > 0:
                    logger.debug(f"Trigger触发点位置: {trigger_positions}, 触发点时间戳: {[packet.time_stamp + int(pos * 1000 / packet.sample_rate) for pos in trigger_positions]}")
                
            eeg = [
                [
                    int.from_bytes(b_eeg[offset + step * j + 4 +  k * packet.resolution : offset + step * j + 7 +  k * packet.resolution], 'big', signed=True)
                    for j in range(packet.sample_num)
                ]
                for k in range(channel_size)
            ]
            packet.eeg = packet.eeg + eeg if packet.eeg else eeg
            
            offset += 4 + channel_size * packet.resolution 
            
        logger.trace(packet)
        return packet
    
  
class C256ImpedancePacket(Packet):
    def __init__(self):
        super().__init__()
        self.impedance = None
        
    @staticmethod
    def transfer(body:bytes) -> 'ImpedancePacket':
        packet = ImpedancePacket()
        packet.time_stamp = int.from_bytes(body[0:8], 'little')
        # packet.result = body[8]
        packet.pkg_id = int.from_bytes(body[9: 13], 'little')
        packet.channels = to_channels(body[13: 45])
        # packet.sample_rate = int.from_bytes(body[45: 49], 'little')
        # packet.sample_len = int.from_bytes(body[49: 53], 'little')
        # packet.resolution = int(int(body[53]) / 8)
        # packet.filter = int(int(body[54]) / 8)
        # packet.wave_type = int(int(body[55]) / 8)
        # packet.wave_freq = int.from_bytes(body[56: 60], 'little')
        # packet.data_len = int.from_bytes(body[60: 64], 'little')
        b_impedance = body[64:]
        packet.impedance = [int.from_bytes(b_impedance[j : j + 4], 'little', signed=False) for j in range(len(packet.channels))]

        logger.trace(f"impedance: {packet}")

    def __str__(self):
        return f"""
            time_stamp: {self.time_stamp}
            pkg_id: {self.pkg_id}
            result: {self.result}
            channels: {self.channels}
            data len: {self.data_len}
            impedance: {self.impedance}
        """
            