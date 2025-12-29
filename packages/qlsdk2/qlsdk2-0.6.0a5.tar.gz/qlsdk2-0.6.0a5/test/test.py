from enum import Enum
from bitarray import bitarray
from loguru import logger

# 通道数组[1,2,3,...]转换为bytes
def to_bytes(channels: list[int], upper=256) -> bytes:
    byte_len = int(upper / 8)
    channel = [0] * byte_len
    result = bitarray(upper)
    result.setall(0)
    for i in range(len(channels)):
        if channels[i] > 0 and channels[i] <= upper: 
            # 每个字节从低位开始计数
            m = (channels[i] - 1) % 8
            result[channels[i] + 6 - 2 * m] = 1
    return result.tobytes()

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
    SQUARE = 1
    AC = 2
    CUSTOM = 3
    PULSE = 4

 # 刺激通道 
class StimulationChannel(object):
    def __init__(self, channel_id: int, waveform: int, current: float, duration: float, ramp_up: float = None, ramp_down: float = None,
                 frequency: float = None, phase_position: int = None, duration_delay: float = None, pulse_width: int = None, pulse_width_rate: int = 1):
        self.channel_id = channel_id
        self.waveform = waveform
        self.current_max = current
        self.current_min = current
        self.duration = duration
        self.ramp_up = ramp_up
        self.ramp_down = ramp_down
        self.frequency = frequency
        self.phase_position = phase_position
        self.duration_delay = duration_delay
        self.pulse_width = pulse_width 
        self.delay_time = 0
        self.pulse_interval = 0
        self.with_group_repeats = 1
        self.pulse_width_rate = 1065353216
        self.pulse_time_f = 0
        self.pulse_time_out = 0
        self.pulse_time_idle = 0
    
    def to_bytes(self):
        # Convert the object to bytes for transmission
        result = self.channel_id.to_bytes(1, 'little')
        wave_form = WaveForm.SQUARE.value if self.waveform == WaveForm.PULSE.value else self.waveform
        result += wave_form.to_bytes(1, 'little')
        result += int(self.current_max * 1000 * 1000).to_bytes(4, 'little')
        # result += int(self.current_min * 1000).to_bytes(2, 'little')
        result += int(self.frequency).to_bytes(2, 'little')
        result += int(self.pulse_width).to_bytes(2, 'little')
        result += int(self.pulse_width_rate).to_bytes(4, 'little')
        
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
    
    def to_json(self):
        return {
            "channel_id": self.channel_id,
            "waveform": self.waveform,
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
        self.characteristic = 0
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
import struct    
if __name__ == "__main__":
    src = bytes.fromhex("0000a040")
    logger.info(f"src: {src}")
    result = struct.unpack("<f", src)[0]
    logger.info(f"result: {result}")
    logger.info(f"result: {struct.pack('<f', result).hex()}")

