from abc import ABC, abstractmethod

class IParser(ABC):
    def __init__(self):
        super().__init__()        
        
    @abstractmethod
    def append(self, buffer):
        pass 
    
    def set_device(self, device):
        pass
    
    def start(self):
        pass
    
    def stop(self):
        pass