from qlsdk.sdk.ar4sdk import AR4SDK, LMDevice


from time import sleep, time
from threading import Lock, Timer
from loguru import logger

class Hub(object):
    def __init__(self):
        self._lock = Lock()
        self._search_timer = None 
        self._search_running = False
        self._devices: dict[str, LMDevice] = {}
    
    @property
    def devices(self):
        return self._devices
    
    def search(self):
        if not self._search_running:
            self._search_running = True
            self._search()
        
    def _search(self):
        if self._search_running:

            self._search_timer = Timer(2, self._search_device)
            self._search_timer.daemon = True
            self._search_timer.start()
        
        
    def _search_device(self):
        try:                        
            devices = AR4SDK.enum_devices()
            # logger.debug(f"_search_ar4 devices size: {len(devices)}")
            for dev in devices:
                self.add_device(hex(dev.mac))
        except Exception as e:
            logger.error(f"_search_device 异常: {str(e)}")
        finally:
            self._search()
            
    def add_device(self, mac: str):
        if mac in list(self._devices.keys()):
            self._devices[mac].update_info()
            logger.info(f"update device mac: {mac}")
        else:
            dev = LMDevice(mac)
            if dev.init():
                self._devices[mac] = dev
                logger.info(f"add device mac: {dev}")
