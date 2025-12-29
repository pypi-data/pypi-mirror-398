from enum import Enum
from abc import ABC, abstractmethod
from loguru import logger
import struct

from qlsdk.core import to_bytes, to_channels

class C64Channel(Enum):
    CH0 = 0
    CH1 = 1
    CH2 = 2
    CH3 = 3
    CH4 = 4
    CH5 = 5
    CH6 = 6
    CH7 = 7
    CH8 = 8
    CH9 = 9
    CH10 = 10
    CH11 = 11
    CH12 = 12
    CH13 = 13
    CH14 = 14
    CH15 = 15

class WaveForm(Enum):
    DC = 0
    PULSE = 1
    AC = 2
    SQUARE = 3
    
class StimulationChannel(ABC):
    def __init__(self, channel_id: int, wave_form: int, current: float, duration: float, ramp_up: float = None, ramp_down: float = None,):
        self.channel_id = channel_id
        self.wave_form = wave_form
        self.current_max = current
        self.current_min = 0
        self.duration = duration
        self.ramp_up = ramp_up
        self.ramp_down = ramp_down
        self.delay_time = 0
        self.frequency = 0
        self.phase_position = 0
        # 预留值，用作占位
        self.reserved = 0
    
    def to_bytes(self):        
        result = self.channel_id.to_bytes(1, 'little')
        result += self.wave_form.to_bytes(1, 'little')
        result += int(self.current_max * 1000 ).to_bytes(2, 'little', signed = True)
        result += int(self.current_min * 1000 ).to_bytes(2, 'little', signed = True)
        result += struct.pack('<f', self.frequency)
        result += struct.pack('<f', self.phase_position)
        
        result += self._ext_bytes()
        
        result += int(self.delay_time).to_bytes(4, 'little')
        result += int(self.ramp_up * 1000).to_bytes(4, 'little')
        result += int((self.duration + self.ramp_up)  * 1000).to_bytes(4, 'little')
        result += int(self.ramp_down * 1000).to_bytes(4, 'little')
        
        return result
    
    def to_bytes_c256(self):        
        result = self.channel_id.to_bytes(1, 'little')
        result += self.wave_form.to_bytes(1, 'little')
        
        result += self._to_bytes_c256()
        
        result += int(self.delay_time).to_bytes(4, 'little')
        result += int(self.ramp_up * 1000).to_bytes(4, 'little')
        result += int((self.duration + self.ramp_up)  * 1000).to_bytes(4, 'little')
        result += int(self.ramp_down * 1000).to_bytes(4, 'little')
        
        return result
    
    def _to_bytes_c256(self):
        return bytes.fromhex("00000000000000000000000000000000000000000000000000000000")
    
    def _ext_bytes(self):
        return bytes.fromhex("00000000000000000000000000000000")
    
    def to_json(self):
        pass
        
    def from_json(self, param):
        pass
    
    def __str__(self):
        return f"ACStimulation(channel_id={self.channel_id}, waveform={self.waveform}, current={self.current_max}, duration={self.duration}, ramp_up={self.ramp_up}, ramp_down={self.ramp_down}, frequency={self.frequency}, phase_position={self.phase_position}, duration_delay={self.duration_delay})"
        
        
        
# 刺激模式-直流
class DCStimulation(StimulationChannel):
    '''
        channel_id: int,  通道编号，从0开始
        current: float,  电流值，单位为mA
        duration: float,  刺激时间，单位为秒
        ramp_up: float,  上升时间，单位为秒
        ramp_down: float,  下降时间，单位为秒
    '''
    def __init__(self, channel_id: int, current: float, duration: float, ramp_up: float = 0, ramp_down: float = 0):
        super().__init__(channel_id, WaveForm.DC.value, current, duration, ramp_up, ramp_down)
    def to_json(self):
        return {
            "channel_id": self.channel_id,
            "waveform": self.wave_form,
            "current_max": self.current_max,
            "duration": self.duration,
            "ramp_up": self.ramp_up,
            "ramp_down": self.ramp_down,
            "frequency": self.frequency,
            "phase_position": self.phase_position,
            "delay_time": self.delay_time
        }
        
    def _to_bytes_c256(self):
        return int(self.current_max * 1000 ).to_bytes(2, 'little') + bytes.fromhex("0000000000000000000000000000000000000000000000000000")
        
    def from_json(self, param):
        pass
    def __str__(self):
        return f"ACStimulation(channel_id={self.channel_id}, waveform={self.waveform}, current={self.current_max}, duration={self.duration}, ramp_up={self.ramp_up}, ramp_down={self.ramp_down}, frequency={self.frequency}, phase_position={self.phase_position}, duration_delay={self.duration_delay})"
        

# 刺激模式-方波
class SquareWaveStimulation(StimulationChannel):
    '''
        channel_id: int,  通道编号，从0开始
        current: float,  电流值，单位为mA
        duration: float,  刺激时间，单位为秒
        ramp_up: float,  上升时间，单位为秒
        ramp_down: float,  下降时间，单位为秒
        frequency: float,  频率，单位为Hz
        duty_cycle: float,  占空比，高电平时间/周期，范围(0, 100)
    '''
    def __init__(self, channel_id: int, current: float, duration: float, ramp_up: float = 0, ramp_down: float = 0,
                 frequency: float = None, duty_cycle: float = 0.5):
        super().__init__(channel_id, WaveForm.SQUARE.value, current, duration, ramp_up, ramp_down)
        self.frequency = frequency
        self.duty_cycle = duty_cycle
        
        
    def to_bytes(self):
        # Convert the object to bytes for transmission
        result = self.channel_id.to_bytes(1, 'little')
        result += self.wave_form.to_bytes(1, 'little')
        result += int(self.current_max * 1000 * 1000).to_bytes(4, 'little', signed = True)
        # result += int(self.current_min * 1000).to_bytes(2, 'little')
        result += int(self.frequency).to_bytes(2, 'little')
        result += int(self.reserved).to_bytes(2, 'little')
        result += struct.pack('<f', self.duty_cycle)
        
        result += self._ext_bytes()
        
        result += int(self.delay_time).to_bytes(4, 'little')
        result += int(self.ramp_up * 1000).to_bytes(4, 'little')
        result += int((self.duration + self.ramp_up)  * 1000).to_bytes(4, 'little')
        result += int(self.ramp_down * 1000).to_bytes(4, 'little')
        
        return result      
    
    def _to_bytes_c256(self):
        result = int(self.current_max * 1000000 ).to_bytes(4, 'little')
        result += int(self.frequency).to_bytes(2, 'little')
        result += bytes.fromhex("0000")
        result += struct.pack('<f', self.duty_cycle)
        result = int(self.current_min * 1000000 ).to_bytes(4, 'little')
        result += self._ext_bytes()
        return  result
    
      
# 刺激模式-正弦
class ACStimulation(StimulationChannel):
    '''
        channel_id: int,  通道编号，从0开始
        current: float,  电流值，单位为mA
        duration: float,  刺激时间，单位为秒
        ramp_up: float,  上升时间，单位为秒
        ramp_down: float,  下降时间，单位为秒
        frequency: float,  频率，单位为Hz
        phase_position: int,  相位位置，单位为度
    '''
    
    def __init__(self, channel_id: int, current: float, duration: float, ramp_up: float = 0, ramp_down: float = 0,
                 frequency: float = None, phase_position: int = 0):
        super().__init__(channel_id, WaveForm.AC.value, current, duration, ramp_up, ramp_down)
        self.current_max = abs(current)
        self.current_min = -abs(current)
        self.frequency = frequency
        # self.frequency = frequency
        self.phase_position = phase_position
    
    def to_json(self):
        return {
            "channel_id": self.channel_id,
            "waveform": self.wave_form,
            "current_max": self.current_max,
            "duration": self.duration,
            "ramp_up": self.ramp_up,
            "ramp_down": self.ramp_down,
            "frequency": self.frequency,
            "phase_position": self.phase_position
        }
        
    def from_json(self, param):
        pass
    
    def _to_bytes_c256(self):
        result = int(self.current_max * 1000 ).to_bytes(2, 'little')
        result += bytes.fromhex("0000")
        result += struct.pack('<f', self.frequency)
        result += struct.pack('<f', self.phase_position)
        result += self._ext_bytes()
        return  result
    
    def __str__(self):
        return f"ACStimulation(channel_id={self.channel_id}, waveform={self.waveform}, current={self.current_max}, duration={self.duration}, ramp_up={self.ramp_up}, ramp_down={self.ramp_down}, frequency={self.frequency}, phase_position={self.phase_position}, duration_delay={self.duration_delay})"
        
# 刺激模式-脉冲
class PulseStimulation(StimulationChannel):
    '''
        channel_id: int,  通道编号，从0开始
        current: float,  电流值，单位为mA
        duration: float,  刺激时间，单位为秒
        frequency: float,  频率，单位为Hz
        pulse_width: int,  脉冲宽度，单位为uS
        pulse_width_ratio: float,  脉冲宽度比，范围(0, 1)
        pulse_interval: int 脉冲间隔，单位为uS
        ramp_up: float,  上升时间，单位为秒
        ramp_down: float,  下降时间，单位为秒
        delay_time: float,  延迟启动时间，单位为秒（暂未启用）
    '''
    def __init__(self, channel_id: int, current: float, duration: float, frequency: float,  pulse_width: int, 
                 pulse_width_ratio: float = 1, pulse_interval: int = 0, ramp_up: float = 0, ramp_down: float = 0, delay_time = 0):
        super().__init__(channel_id, WaveForm.PULSE.value, current, duration, ramp_up, ramp_down)
        self.frequency = frequency
        self.delay_time = delay_time
        self.pulse_width = pulse_width 
        self.pulse_width_ratio = pulse_width_ratio
        self.pulse_interval = pulse_interval
        self.with_group_repeats = 1
        self.pulse_time_f = 0
        self.pulse_time_out = 0
        self.pulse_time_idle = 0
        
    def to_bytes(self):
        # Convert the object to bytes for transmission
        result = self.channel_id.to_bytes(1, 'little')
        result += self.wave_form.to_bytes(1, 'little')
        result += int(self.current_max * 1000 * 1000).to_bytes(4, 'little', signed = True)
        # result += int(self.current_min * 1000).to_bytes(2, 'little')
        result += int(self.frequency).to_bytes(2, 'little')
        result += int(self.pulse_width).to_bytes(2, 'little')
        result += struct.pack('<f', self.pulse_width_ratio)
        
        result += int(self.pulse_interval).to_bytes(2, 'little')
        result += int(self.with_group_repeats).to_bytes(2, 'little')
        result += int(self.pulse_time_f).to_bytes(4, 'little')
        result += int(self.pulse_time_out).to_bytes(4, 'little')
        result += int(self.pulse_time_idle).to_bytes(4, 'little')
        
        result += int(self.delay_time).to_bytes(4, 'little')
        result += int(self.ramp_up * 1000).to_bytes(4, 'little')
        result += int((self.duration + self.ramp_up)  * 1000).to_bytes(4, 'little')
        result += int(self.ramp_down * 1000).to_bytes(4, 'little')
        
        return result
    
    def _to_bytes_c256(self):
        result = int(self.current_max * 1000000 ).to_bytes(4, 'little')
        result += int(self.frequency).to_bytes(2, 'little')
        result += bytes.fromhex("0000")
        result += struct.pack('<f', self.duty_cycle)
        result = int(self.current_min * 1000000 ).to_bytes(4, 'little')
        result += self._ext_bytes()
        return  result
    
    def to_json(self):
        return {
            "channel_id": self.channel_id,
            "wave_form": self.wave_form,
            "current_max": self.current_max,
            "current_min": self.current_min,
            "duration": self.duration,
            "ramp_up": self.ramp_up,
            "ramp_down": self.ramp_down,
            "frequency": self.frequency,
            "phase_position": self.phase_position,
            "duration_delay": self.duration_delay,
            "pulse_width": self.pulse_width,
            "delay_time": self.delay_time,
            "pulse_interval": self.pulse_interval,
            "with_group_repeats": self.with_group_repeats
        }
    
        
# 刺激范式
class StimulationParadigm(object):
    def __init__(self):
        self.channels = None
        self.duration = None
        self.interval_time = 0
        self.characteristic = 1
        self.mode = 0
        self.repeats = 0
        
    def add_channel(self, channel: StimulationChannel, update=False):
        if self.channels is None:
            self.channels = {}
        channel_id = channel.channel_id + 1
        if channel_id in self.channels.keys():
            logger.warning(f"Channel {channel_id} already exists")
            if update:
                self.channels[channel_id] = channel
        else:
            self.channels[channel_id] = channel  
            
        # 计算刺激时间
        duration = channel.duration + channel.ramp_up + channel.ramp_down     
        if self.duration is None or duration > self.duration:
            self.duration = duration 
        
        
    def to_bytes(self):
        result = to_bytes(list(self.channels.keys()), 64)
        result += int(self.duration * 1000).to_bytes(4, 'little')
        result += int(self.interval_time).to_bytes(4, 'little')
        result += int(self.characteristic).to_bytes(4, 'little')
        result += int(self.mode).to_bytes(1, 'little')
        result += int(self.repeats).to_bytes(4, 'little')
        for channel in self.channels.values():
            result += channel.to_bytes()
        return result
    
    def to_bytes_c256(self):
        result = to_bytes(list(self.channels.keys()), 256)
        result += int(self.duration * 1000).to_bytes(4, 'little')
        result += int(self.interval_time).to_bytes(4, 'little')
        result += int(self.characteristic).to_bytes(4, 'little')
        result += int(self.mode).to_bytes(1, 'little')
        result += int(self.repeats).to_bytes(4, 'little')
        for channel in self.channels.values():
            result += channel.to_bytes()
        return result
    
    def to_json(self):
        # Convert the object to JSON for transmission
        return {
            "channels": list(self.channels.keys()),
            "duration": self.duration,
            "interval_time": self.interval_time,
            "characteristic": self.characteristic,
            "mode": self.mode,
            "repeats": self.repeats, 
            "stim": [channel.to_json() for channel in self.channels.values()]
        }
        
    # @staticmethod
    # def from_json(param: Dict[str, Any]):
    #     pass
    
    def clear(self):
        self.channels = None
        self.duration = None
        self.interval_time = 25000
        self.characteristic = 1
        self.mode = 0
        self.repeats = 0


# 刺激范式
class C256StimulationParadigm(object):
    def __init__(self):
        self.channels = None
        self.duration = None
        self.interval_time = 0
        self.characteristic = 1
        self.mode = 0
        self.repeats = 0
        
    def add_channel(self, channel: StimulationChannel, update=False):
        if self.channels is None:
            self.channels = {}
        channel_id = channel.channel_id + 1
        if channel_id in self.channels.keys():
            logger.warning(f"Channel {channel_id} already exists")
            if update:
                self.channels[channel_id] = channel
        else:
            self.channels[channel_id] = channel  
            
        # 计算刺激时间
        duration = channel.duration + channel.ramp_up + channel.ramp_down     
        if self.duration is None or duration > self.duration:
            self.duration = duration 
        
        
    def to_bytes(self):
        result = to_bytes(list(self.channels.keys()), 64)
        result += int(self.duration * 1000).to_bytes(4, 'little')
        result += int(self.interval_time).to_bytes(4, 'little')
        result += int(self.characteristic).to_bytes(4, 'little')
        result += int(self.mode).to_bytes(1, 'little')
        result += int(self.repeats).to_bytes(4, 'little')
        for channel in self.channels.values():
            result += channel.to_bytes()
        return result
    
    def to_json(self):
        # Convert the object to JSON for transmission
        return {
            "channels": list(self.channels.keys()),
            "duration": self.duration,
            "interval_time": self.interval_time,
            "characteristic": self.characteristic,
            "mode": self.mode,
            "repeats": self.repeats, 
            "stim": [channel.to_json() for channel in self.channels.values()]
        }
        
    # @staticmethod
    # def from_json(param: Dict[str, Any]):
    #     pass
    
    def clear(self):
        self.channels = None
        self.duration = None
        self.interval_time = 0
        self.characteristic = 1
        self.mode = 0
        self.repeats = 0