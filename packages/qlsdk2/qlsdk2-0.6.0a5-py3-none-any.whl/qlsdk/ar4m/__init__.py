from qlsdk.sdk import Hub
from qlsdk.ar4 import AR4
from loguru import logger


class AR4M(Hub):
    def __init__(self):
        super().__init__()
        self._devices: dict[str, AR4] = {}
        self._search_running = False
        self._search_timer = None
    
    def add_device(self, mac: str):
        if mac in list(self._devices.keys()):
            self._devices[mac].update_info()
            logger.debug(f"update x8 device mac: {mac}")
        else:
            dev = AR4(mac)
            if dev.connected:
                self._devices[mac] = dev
                logger.info(f"add x8 device mac: {dev}")