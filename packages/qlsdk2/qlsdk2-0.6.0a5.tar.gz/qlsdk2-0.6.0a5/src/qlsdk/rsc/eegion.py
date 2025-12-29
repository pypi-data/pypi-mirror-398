import socket
import json
import threading
import logging
import time
import queue
from abc import ABC, abstractmethod
from typing import Dict, List, Callable, Optional, Tuple
from loguru import logger

from rsc import UdpBroadcaster

# ----------------------
# Constants and Exceptions
# ----------------------
UDP_DISCOVERY_PORT = 50000
TCP_COMMUNICATION_PORT = 50001
PROXY_PORT = 50002
BUFFER_SIZE = 4096

class DeviceError(Exception):
    """Base exception for device related errors"""

class DeviceNotFoundError(DeviceError):
    """Requested device not found"""

class ConnectionError(DeviceError):
    """Device connection failure"""

class UnsupportedFeatureError(DeviceError):
    """Requested feature not supported"""
    
# ----------------------
# Data Structures
# ----------------------
class DeviceInfo:
    def __init__(self, serial: str, device_type: str, ip: str, tcp_port: int):
        self.serial = serial
        self.type = device_type
        self.ip = ip
        self.tcp_port = tcp_port

    def __repr__(self):
        return f"<Device {self.serial} ({self.type}) @ {self.ip}:{self.tcp_port}>"
    
    
class SecureTCPConnection:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self._socket = None
        self._lock = threading.Lock()
        self._connected = False
        self._logger = logging.getLogger("Connection")
        self._message_queue = queue.Queue()
        self._receive_thread = None

    def connect(self):
        """Establish and maintain TCP connection"""
        with self._lock:
            if self._connected:
                return

            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self._socket.connect((self.ip, self.port))
                self._connected = True
                self._start_receive_thread()
            except socket.error as e:
                raise ConnectionError(f"Connection failed: {str(e)}")

    def _start_receive_thread(self):
        self._receive_thread = threading.Thread(
            target=self._receive_worker,
            daemon=True
        )
        self._receive_thread.start()

    def _receive_worker(self):
        while self._connected:
            try:
                data = self._socket.recv(BUFFER_SIZE)
                if not data:
                    break
                self._message_queue.put(data)
            except (socket.error, ConnectionResetError):
                break
        self.disconnect()

    def disconnect(self):
        """Close TCP connection"""
        with self._lock:
            if self._connected and self._socket:
                self._socket.close()
                self._connected = False

    def send(self, data: bytes):
        """Send data through TCP connection"""
        with self._lock:
            if not self._connected:
                raise ConnectionError("Not connected")
            try:
                self._socket.sendall(data)
            except socket.error as e:
                raise ConnectionError(f"Send failed: {str(e)}")

    def receive(self) -> Optional[bytes]:
        """Get received data from queue"""
        try:
            return self._message_queue.get_nowait()
        except queue.Empty:
            return None

# ----------------------
# Device Abstraction Layer
# ----------------------
class BaseDevice(ABC):
    def __init__(self, info: DeviceInfo, connection: SecureTCPConnection):
        self.info = info
        self.conn = connection
        self._data_callbacks: List[Callable[[bytes], None]] = []
        self._command_callbacks: List[Callable[[dict], None]] = []
        self._stream_active = False
        self._stream_thread: Optional[threading.Thread] = None

    @property
    @abstractmethod
    def supports_acquisition(self) -> bool:
        pass

    @property
    @abstractmethod
    def supports_stimulation(self) -> bool:
        pass

    def register_data_callback(self, callback: Callable[[bytes], None]):
        self._data_callbacks.append(callback)

    def register_command_callback(self, callback: Callable[[dict], None]):
        self._command_callbacks.append(callback)

    # 启动信号采集
    def start_acq(self, persist=False, path=None):    
        self.send_command({"type": "acquire", "param": "start", "value": persist})
        if not self.supports_acquisition:
            raise UnsupportedFeatureError("signal acquisition not supported")

        self._stream_active = True
        self._stream_thread = threading.Thread(
            target=self._stream_worker,
            daemon=True
        )
        self._stream_thread.start()
      
    # 停止信号采集  
    def stop_acq(self):    
        self._stream_active = False
        if self._stream_thread:
            self._stream_thread.join()
    
    # 设置信号采集配置
    def set_acq_config(self, config: dict): 
        """Set data acquisition configuration"""
        self.send_command({"type": "acquire", "param": "config", "value": config})

    # 设置电刺激配置
    def set_stim_config(self, config: dict):
        """Set stimulation configuration"""
        self.send_command({"type": "stim", "param": "config", "value": config})

    def start_stim(self):
        """Start stimulation"""
        self.send_command({"type": "stim", "param": "start"})

    def _stream_worker(self):
        while self._stream_active:
            data = self.conn.receive()
            if data:
                for callback in self._data_callbacks:
                    callback(data)
            time.sleep(0.001)

    def send_command(self, command: dict):
        """Send command and notify callbacks"""
        try:
            self.conn.send(json.dumps(command).encode())
            for callback in self._command_callbacks:
                callback(command)
        except ConnectionError as e:
            logging.error(f"Command failed: {str(e)}")

# ----------------------
# Device Implementations
# ----------------------
class LJS1(BaseDevice):
    @property
    def supports_acquisition(self) -> bool:
        return True

    @property
    def supports_stimulation(self) -> bool:
        return False

    def set_sampling_rate(self, rate: int):
        self.send_command({"type": "config", "param": "rate", "value": rate})

class ARS(BaseDevice):
    @property
    def supports_acquisition(self) -> bool:
        return True

    @property
    def supports_stimulation(self) -> bool:
        return False
    def set_stimulation(self, intensity: float, duration: float):
        self.send_command({
            "type": "stimulate",
            "intensity": intensity,
            "duration": duration
        })

class X8(BaseDevice):
    @property
    def supports_acquisition(self) -> bool:
        return True

    @property
    def supports_stimulation(self) -> bool:
        return False
    def set_stimulation(self, intensity: float, duration: float):
        self.send_command({
            "type": "stimulate",
            "intensity": intensity,
            "duration": duration
        })
 
class C64RS(BaseDevice):
    @property
    def supports_acquisition(self) -> bool:
        return True

    @property
    def supports_stimulation(self) -> bool:
        return False
    def set_stimulation(self, intensity: float, duration: float):
        self.send_command({
            "type": "stimulate",
            "intensity": intensity,
            "duration": duration
        })       
        
class C256RS(BaseDevice):
    @property
    def supports_acquisition(self) -> bool:
        return True

    @property
    def supports_stimulation(self) -> bool:
        return False
    def set_stimulation(self, intensity: float, duration: float):
        self.send_command({
            "type": "stimulate",
            "intensity": intensity,
            "duration": duration
        })

# ----------------------
# Proxy Server
# ----------------------
class DeviceProxy:
    def __init__(self, sdk):
        self.sdk = sdk
        self._running = False
        self._server_socket = None
        self._clients = {}
        self._logger = logging.getLogger("DeviceProxy")

    def start(self, port: int = PROXY_PORT):
        self._running = True
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('0.0.0.0', port))
        self._server_socket.listen(5)
        threading.Thread(target=self._accept_clients, daemon=True).start()

    def stop(self):
        self._running = False
        if self._server_socket:
            self._server_socket.close()

    def _accept_clients(self):
        while self._running:
            try:
                client_socket, addr = self._server_socket.accept()
                client_id = f"{addr[0]}:{addr[1]}"
                self._clients[client_id] = client_socket
                threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr),
                    daemon=True
                ).start()
            except OSError:
                break

    def _handle_client(self, client_socket: socket.socket, addr: Tuple[str, int]):
        client_id = f"{addr[0]}:{addr[1]}"
        self._logger.info(f"New client connected: {client_id}")

        while self._running:
            try:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break

                # Process proxy command
                try:
                    command = json.loads(data.decode())
                    self._process_command(client_socket, command)
                except json.JSONDecodeError:
                    self._logger.warning(f"Invalid command from {client_id}")

            except (ConnectionResetError, socket.error):
                break

        self._logger.info(f"Client disconnected: {client_id}")
        client_socket.close()
        del self._clients[client_id]

    def _process_command(self, client_socket: socket.socket, command: dict):
        required_fields = ["device_id", "action", "params"]
        if not all(field in command for field in required_fields):
            self._logger.warning("Invalid command structure")
            return

        try:
            device = self.sdk.get_device(command["device_id"])
            if not device:
                raise DeviceNotFoundError

            # Execute device command
            if command["action"] == "send":
                device.send_command(command["params"])
                client_socket.send(b"Command executed")
            elif command["action"] == "stream":
                self._setup_streaming(client_socket, device)
            else:
                client_socket.send(b"Invalid action")

        except DeviceError as e:
            client_socket.send(f"Error: {str(e)}".encode())

    def _setup_streaming(self, client_socket: socket.socket, device: BaseDevice):
        def forward_data(data: bytes):
            try:
                client_socket.send(data)
            except (socket.error, ConnectionResetError):
                device.stop_data_stream()

        device.register_data_callback(forward_data)
        device.start_data_stream()
        client_socket.send(b"Streaming started")