from abc import ABC, abstractmethod

class IHandler(ABC):
    def __init__(self):
        super().__init__()        
        
    @abstractmethod
    def handler(self, buffer):
        pass 