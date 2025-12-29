from abc import ABC, abstractmethod

class ICommand(ABC):
    def __init__(self):
        super().__init__()
        
        
    @abstractmethod
    def append(self, buffer):
        pass 