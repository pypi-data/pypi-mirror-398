from loguru import logger
from threading import Thread, Lock
import socket

class DeviceProxy(object):
    def __init__(self, client_socket):
        self.client_socket = client_socket
        self.server_socket = None   
        # 客户端设备
        # self.device = QLDevice(client_socket)
        # self.parser = DeviceParser(self.device)
        
        self._init_server()
        
    def _init_server(self):
        # 连接目标服务（桌面端运行在本地的18125端口）
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect(('localhost', 18125))
    
    def start(self):
        logger.info("DeviceProxy连接已建立")
        
        try:            
            # 创建双向转发线程
            client_thread = Thread(
                target=self.data_forward,
                args=(self.client_socket, self.server_socket, "设备->软件")
            )
            server_thread = Thread(
                target=self.data_forward,
                args=(self.server_socket, self.client_socket, "软件->设备")
            )

            # 启动线程
            client_thread.start()
            server_thread.start()

            # 等待线程结束
            client_thread.join()
            server_thread.join()
            
        except Exception as e:
            logger.error(f"连接异常: {str(e)}")
            self.client_socket.close()      
        finally:
            logger.error(f"连接已结束")
            self.client_socket.close()
            
    def data_forward(self, src, dest, direction, callback=None):
        """
        数据转发函数
        :param src: 源socket连接
        :param dest: 目标socket连接
        :param direction: 转发方向描述
        """
        try:
            logger.debug(f"[{direction}] 转发开始")
            while True:
                data = src.recv(4096*1024)  # 接收数据缓冲区设为4KB
                if not data:
                    break
                logger.info(f"[{direction}] 转发指令: {hex(int.from_bytes(data[12:14], 'little'))} ")
                logger.debug(f"[{direction}] 转发 {data.hex()} ")
                if callback:
                    callback(data)
                dest.sendall(data)
                logger.debug(f"[{direction}] 转发 {len(data)} 字节")
        except ConnectionResetError:
            logger.error(f"[{direction}] 连接已关闭")
        finally:
            src.close()
            dest.close()
            
    # def device_message(self, data):     
    #     # 解析数据包
    #     self.parser.append(data)