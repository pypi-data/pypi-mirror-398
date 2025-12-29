from typing import Dict, Type
from qlsdk.rsc.interface import IDevice

from qlsdk.rsc.device.c64_rs import C64RS
from qlsdk.rsc.device.arskindling import ARSKindling

from loguru import logger

class DeviceFactory(object):    
    """Registry for device implementations"""
    _devices: Dict[str, Type[IDevice]] = {}
    
    @classmethod
    def register(cls, device_type: int, device: Type[IDevice]):
        cls._devices[device_type] = device
    
    @classmethod
    def create_device(cls, device: IDevice) -> Type[IDevice]:
        logger.trace(f"Creating device for device type: {hex(device.device_type)}, support types: {cls._devices.keys()}")
        if device.device_type not in cls._devices.keys():
            logger.warning(f"不支持的设备类型: {hex(device.device_type)}")
            raise ValueError(f"Unsupported device type: {hex(device.device_type)}")
        
        instance = cls._devices[device.device_type]
        return instance.from_parent(device) if hasattr(instance, 'from_parent') else instance(device.socket)

# Register the C64RS device with the DeviceFactory    
DeviceFactory.register(C64RS.device_type, C64RS)
# Register the ARSKindling device with the DeviceFactory
DeviceFactory.register(ARSKindling.device_type, ARSKindling) 



    
    