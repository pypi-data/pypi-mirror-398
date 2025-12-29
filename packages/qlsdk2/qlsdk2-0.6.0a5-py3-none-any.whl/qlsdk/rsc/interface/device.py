from abc import ABC, abstractmethod
import abc
from typing import Literal

class  IDevice(ABC):     
    
    @property
    @abc.abstractmethod   
    def device_type(self) -> int:
        pass
    
    def set_device_type(self, value: int):
        raise NotImplementedError("Not Supported")
    
    def set_storage_path(self, path: str):
        raise NotImplementedError("Not Supported")
    
    def set_file_prefix(self, pre: str):
        raise NotImplementedError("Not Supported")
    
    def set_acq_param(self, channels, sample_rate = 500, sample_range = 188):
        raise NotImplementedError("Not Supported")
    
    @property
    def device_no(self) -> str:
        pass
    
    def read_msg(self, size: int) -> bytes:
        raise NotImplementedError("Not Supported")
        
    def produce(self, body: bytes, type:Literal['signal', 'impedance']="signal") -> None:
        raise NotImplementedError("Not Supported")
    
    def start_listening(self):
        raise NotImplementedError("Not Supported")
    
    def stop_listening(self):
        raise NotImplementedError("Not Supported")
    
    def set_device_no(self, value: str):
        raise NotImplementedError("Not Supported")
    
    def from_parent(cls, parent) :
        raise NotImplementedError("Not Supported")
    
    def start_acquisition(self) -> None:
        raise NotImplementedError("Not Supported")
    
    def stop_acquisition(self) -> None:
        raise NotImplementedError("Not Supported")
    
    def subscribe(self, type="signal") -> None:
        raise NotImplementedError("Not Supported")
    def unsubscribe(self, topic) -> None:
        raise NotImplementedError("Not Supported")
    
    def start_stimulation(self, type="signal", duration=0) -> None:
        raise NotImplementedError("Not Supported")
    
    def stop_stimulation(self) -> None:
        raise NotImplementedError("Not Supported")
    def disconnect(self) -> None:
        raise NotImplementedError("Not Supported")
        