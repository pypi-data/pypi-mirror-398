from qlsdk.sdk import Hub
from qlsdk.x8 import X8
from loguru import logger


class X8M(Hub):
    def __init__(self):
        super().__init__()
        self._devices: dict[str, X8] = {}
        self._search_running = False
        self._search_timer = None
    
    def add_device(self, mac: str):
        if mac in list(self._devices.keys()):
            self._devices[mac].update_info()
            logger.debug(f"update x8 device mac: {mac}")
        else:
            dev = X8(mac)
            if dev.connected:
                self._devices[mac] = dev
                logger.info(f"add x8 device mac: {dev}")