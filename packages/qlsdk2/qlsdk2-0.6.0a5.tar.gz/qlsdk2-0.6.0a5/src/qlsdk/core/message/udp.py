
from enum import Enum
from time import timezone
from qlsdk.core.crc import check_crc, crc16
from qlsdk.core.local import get_ip, get_ips

from loguru import logger


class UDPCommand(Enum):
    CONNECT = 0x10
    NOTIFY = 0x09


class UDPMessage(object):
    START = "SHQuanLan"
    MAC = 'mac'
    DEV_TYPE = "dev_type"
    VERSION_CODE = "version_code"
    VERSION_NAME = "version_name"

    def __init__(self) -> None:
        self._base = None
        self._message = None

    @staticmethod
    def parse(packet, address = None):
        plen = len(packet)
        if plen < 10:
            logger.trace("message length too short.")
            return

        start = packet[:9].decode("utf-8")
        # quanlan udp message
        if start != UDPMessage.START:
            return

        if not check_crc(packet):
            logger.warn(f"数据CRC校验失败，丢弃！")
            return
        
        # message command
        cmd = int.from_bytes(packet[10:12], 'little')

        return UDPMessage._parse(cmd, packet[12:])

    @staticmethod
    def _parse(cmd, data):
        # 只解析0x09
        if cmd == UDPCommand.NOTIFY.value:
            return UDPMessage.parseDeviceInfo(data)
        else:
            logger.trace(f'不支持的消息. cmd: {hex(cmd)} dlen: {len(data)} data: {data}')
            return None
        
    @staticmethod
    def parseDeviceInfo(data):
        device_info = {}
        try:
            device_info[UDPMessage.DEV_TYPE] = hex(int.from_bytes(data[:2], 'little'))
            device_info[UDPMessage.MAC] = hex(int.from_bytes(data[2:10], 'little'))
            device_info[UDPMessage.VERSION_CODE] = int.from_bytes(data[42:46], 'little')
            device_info[UDPMessage.VERSION_NAME] = str(data[10:42],'utf-8').split('\x00')[0]
        except Exception as e:
            logger.error(f"parseDeviceInfo异常：{e}")

        return device_info

    @staticmethod
    def search(device_id : str, server_ip : str=None, server_port : int=19216):
        # 服务端Ip
        if server_ip is None:
            server_ip = get_ip()
            
        return UDPMessage._search_(device_id, server_ip, server_port)
    
    @staticmethod
    def _search_(device_id : str, server_ip : str, server_port : int=19216):
        # 服务端Ip
        if server_ip is None:
            raise ValueError("server_ip is None")
            
        logger.debug(f"search device {device_id} on {server_ip}:{server_port}")
            
        message = bytearray(28)
        # 消息头
        message[:10] = UDPMessage.START.encode('utf-8')
        # 消息类型
        message[10:12] = UDPCommand.CONNECT.value.to_bytes(2, 'little')
        # 设备序列号格式沿用现有协议
        serial_no = f'F0{device_id[:2]}FFFFFFFF{device_id[4:]}' 
        message[12:22] = bytes.fromhex(serial_no)
        # 本机ip
        ip = server_ip.split(".")    
        message[22] = (int)(ip[0])
        message[23] = (int)(ip[1])
        message[24] = (int)(ip[2])
        message[25] = (int)(ip[3])
        # 服务端端口（按大端输出）
        message[26:28] = server_port.to_bytes(2, 'big')
        # 校验和（按小端输出）
        checksum = crc16(message).to_bytes(2, 'little')

        return message + checksum