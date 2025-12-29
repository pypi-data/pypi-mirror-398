import socket
import time
from threading import Thread, Lock
from loguru import logger

from qlsdk.core.message import UDPMessage

class UdpBroadcaster:
    # 广播端口需要和ar4sdk做区分， 使用54366时不能和x8同时使用
    def __init__(self, port=54366):
        self.broadcast_port = port
        self.devices_to_broadcast = []  # 待广播的设备序列号列表
        self.connected_devices = set()  # 已连接的设备序列号集合
        self.lock = Lock()  # 用于线程安全的锁
        self.running = True

        # 创建UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def add_device(self, device_id):
        """添加设备序列号到待广播列表"""
        with self.lock:
            if device_id not in self.devices_to_broadcast:
                self.devices_to_broadcast.append(device_id)
                logger.info(f"Added device {device_id} to broadcast list.")

    def remove_device(self, device_id):
        """从待广播列表中移除设备序列号"""
        with self.lock:
            if device_id in self.devices_to_broadcast:
                self.devices_to_broadcast.remove(device_id)
                logger.info(f"Removed device {device_id} from broadcast list.")

    def mark_device_as_connected(self, device_id):
        """将设备标记为已连接，并从未广播列表中移除"""
        with self.lock:
            if device_id in self.devices_to_broadcast:
                self.devices_to_broadcast.remove(device_id)
            self.connected_devices.add(device_id)
            logger.info(f"Device {device_id} is now connected.")

    def broadcast_devices(self):
        """轮询发送广播"""
        while self.running:
            with self.lock:
                for device_id in self.devices_to_broadcast:
                    message = UDPMessage.search(device_id)
                    self.sock.sendto(message, ('<broadcast>', self.broadcast_port))
                    logger.info(f"Broadcasting device ID: {device_id}")
            time.sleep(1)  # 每隔1秒发送一次广播

    def start(self):
        """启动广播线程"""
        self.broadcast_thread = Thread(target=self.broadcast_devices)
        self.broadcast_thread.setDaemon(True)
        self.broadcast_thread.start()

    def stop(self):
        """停止广播"""
        self.running = False
        self.broadcast_thread.join()
        self.sock.close()

# 示例使用
if __name__ == "__main__":
    broadcaster = UdpBroadcaster()

    # 添加设备序列号到待广播列表
    broadcaster.add_device_to_broadcast("390024130032")

    # 启动广播
    broadcaster.start()

    try:
        # 模拟运行一段时间
        time.sleep(10)

        # 标记设备为已连接
        broadcaster.mark_device_as_connected("390024130032")

        # 继续运行一段时间
        time.sleep(10)

    finally:
        # 停止广播
        broadcaster.stop()