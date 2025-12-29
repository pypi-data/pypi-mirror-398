# from abc import ABC, abstractmethod

class BaseDevice(object):
    def __init__(self, socket = None):
        self.socket = socket
        self.device_name = None
        self._device_type = None
        self.device_id = None
        
        
    @property
    def device_type(self) -> int:
        return self._device_type
    
    @device_type.setter
    def device_type(self, value: int):
        self._device_type = value
        
    @property
    def acq_channels(self) :
        return None
    @property
    def sample_range(self) -> int:
        return None
    @property
    def sample_rate(self) -> int:
        return None
    @property
    def sample_num(self) -> int:
        return 10
    @property
    def resolution(self):
        return 24
    