import socket
import time
from threading import Thread, Lock
from loguru import logger

from qlsdk.core.message import UDPMessage
from qlsdk.core.local import get_ips

'''
    广播器类，用于发送和接收设备广播消息
    主要功能：发送设备搜索消息，接收设备连接消息
    注意：广播端口需要和ar4sdk做区分，使用54366时不能和x8同时使用
'''
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

    # 添加设备序列号到待广播列表
    def add_device(self, device_id):
        
        with self.lock:
            if device_id not in self.devices_to_broadcast:
                self.devices_to_broadcast.append(device_id)
                logger.info(f"添加设备[{device_id}]到搜索列表。")

    # 从待广播列表移除设备序列号
    def remove_device(self, device_id):
        
        with self.lock:
            if device_id in self.devices_to_broadcast:
                self.devices_to_broadcast.remove(device_id)
                logger.info(f"把设备[{device_id}]从搜索列表中移除。")

    # 把设备标记为已连接
    def mark_device_as_connected(self, device_id):
        with self.lock:
            # 如果设备已连接，则从搜索列表中移除
            if device_id in self.devices_to_broadcast:
                self.devices_to_broadcast.remove(device_id)
                
            # 添加到已连接设备集合
            self.connected_devices.add(device_id)
            
            logger.info(f"设备[{device_id}]已连接，从搜索列表中移除。")

    # 广播设备信息，寻求配对
    def broadcast_devices(self):
        
        while self.running:
            ips = get_ips()
            with self.lock:
                for device_id in self.devices_to_broadcast:
                    message = UDPMessage.search(device_id)
                    self.sock.sendto(message, ('<broadcast>', self.broadcast_port))
                    logger.debug(f"设备[{device_id}]广播消息已发送。")
                
            # 每隔1秒发送一次广播    
            time.sleep(1)  

    def start(self):
        """启动广播线程"""
        self.broadcast_thread = Thread(target=self.broadcast_devices, daemon=True)
        self.broadcast_thread.start()

    def stop(self):
        """停止广播"""
        self.running = False
        self.broadcast_thread.join()
        self.sock.close()