import sys
if sys.platform == "linux":
    from signal import signal, SIGPIPE, SIG_DFL
    signal(SIGPIPE, SIG_DFL)


import socket
import time
from typing import Literal
import select
from sys import platform
from abc import ABC, abstractmethod
import re
from dataclasses import dataclass
import serial
from time import sleep
from threading import Event
from threading import Event, Lock
import socket
from datetime import datetime, timedelta
# from custom_types import Device

import crcmod

import logging

LOGGER = logging.getLogger("serial-com")

logger = LOGGER

def set_log_level(level=logging.INFO):
    logger.setLevel(level)


def set_logger(new_logger: logging.Logger):
    global LOGGER, logger
    LOGGER = new_logger
    logger = LOGGER


SERIAL_PORT = "serial"
NETWORK_PORT = "network"
PORT_TYPE = Literal[SERIAL_PORT, NETWORK_PORT]
PORT_ACCESS = Event()
PORT_ACCESS.clear()
MIN_TIMEOUT = 0.1
DEFAULT_TIMEOUT = 3
CHECK_CONNECTION_ALIVE_TIMEOUT = 80

class  SocketClosedError(Exception):
    ...


class Port(ABC):
    
    def __init__(self, *args, **kwargs):
        self._last_packet_time = datetime.now()

    @abstractmethod
    def read(self, size=-1, *args, **kwargs) -> bytes:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def write(self, bl: bytes, *args, **kwargs) -> int:
        ...

    @abstractmethod
    def read_until(self, *args, **kwargs) -> None:
        """Read until new line"""
        ...

    @property
    @abstractmethod
    def in_waiting(self) -> int:
        ...

    @property
    def read_timeout(self) -> float:
        ...

    @property
    @abstractmethod
    def out_waiting(self) -> int:
        ...

    @abstractmethod
    def reset_input_buffer(self) -> None:
        ...

    @abstractmethod
    def reset_output_buffer(self) -> None:
        ...

    @abstractmethod
    def open(self):
        ...

    @abstractmethod
    def close(self):
        ...

    @abstractmethod
    def is_open(self):
        ...

    @abstractmethod
    def is_closed(self):
        ...


class SerialPort(serial.Serial):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_packet_time = datetime.now()

    def __call__(self):
        return SerialPort(port=self.port, baudrate=self.baudrate, bytesize=self.bytesize, parity=self.parity,
                          stopbits=self.stopbits, timeout=self.timeout, write_timeout=self.write_timeout)
    
    @property
    def read_timeout(self) -> float:
        return self.timeout
    
    @read_timeout.setter
    def read_timeout(self, timeout: float):
        if not isinstance(timeout, float) or isinstance(timeout, int):
            raise ValueError(F"Invalid timeout of type {type(timeout)}. Expected type float or int")
        self.timeout = timeout
    
    def read_until(self, eol: bytes) -> bytes:
        if eol == b"\r\n":
            return self.readline()
        leneol = len(eol)
        response = bytearray()
        while True:
            ans = self.read(1)
            if not ans:
                logger.info(
                    "Was waiting for %s but stopped reading on timeout and received %s" % (
                        eol.__repr__(), response.__repr__()))
                return
            if ans not in eol:
                continue
            response.append(ans)
            if response[-leneol:] == eol:
                return response


class IPPort(socket.socket):

    chunk_size = 1024

    def __init__(self, *args, addr_port: tuple[str, int]|None = None,
                 read_timeout: float = 0.5, **kwargs):
        """To intialize the object call IPPort()"""
        super(IPPort, self).__init__(socket.AF_INET, socket.SOCK_STREAM, *args, **kwargs)
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.settimeout(read_timeout)
        self.addr_port = addr_port
        self._read_timeout = read_timeout
        self._last_packet_time = datetime.now()

    @property
    def name(self):
        return str(self.addr_port)

    def apply_settings(self, data: dict):
        self.read_timeout = data["timeout"]

    @property
    def read_timeout(self) -> float|None:
        return self.gettimeout()

    @read_timeout.setter
    def read_timeout(self, value: float):
        self.settimeout(value)
    
    
    def read(self, size=chunk_size, *args, **kwargs) -> bytes:
        try:
            ans = super().recv(size)
            if ans == b"":
                # Empty string means the connection was closed by the peer
                raise SocketClosedError("Connection closed by remote host")
                
            self._last_packet_time = datetime.now()
            return ans
            
        except socket.timeout:
            # Check if connection is still alive by last packet time
            return b""
            
        except Exception as e:
            raise SocketClosedError(f"Unexpected error: {e}")
        
        finally:
            self.validate_connection_by_last_time_packet()
            
    def validate_connection_by_last_time_packet(self):
        if (datetime.now() - self._last_packet_time) > timedelta(seconds=CHECK_CONNECTION_ALIVE_TIMEOUT):
            logger.info(f"Long no answer from {self}")
            raise SocketClosedError(f"Connection timeout from {self}")

    def write(self, bl: bytes, *args, **kwargs) -> int:
        try:
            return super().send(bl)
        except OSError as e:
            logger.warning(e)
            # if platform == "win32":
            #     if e.errno in (10038, 10054, 32):  # socket was closed
            #         raise SocketClosedError("Socket was closed. A new one must be created")
            # elif platform == "linux":
            #     if e.errno in (104, 113, 5, 32):
            #         raise SocketClosedError("Socket was closed. A new one must be created")
            raise SocketClosedError(f"{self} Socket was closed. A new one must be created")

    def read_until(self, eol:bytes=b"\r\n") -> bytes:
        leneol = len(eol)
        response = bytearray()
        
        timeout = self.read_timeout
        if timeout is None:
            timeout = DEFAULT_TIMEOUT
        init_time = time.time()
        end_time = init_time + float(timeout)
        while True:
            if time.time() > end_time:
                break
            ans = self.read(1)
            if not ans:
                logger.debug(
                    "Was waiting for %s but stopped reading on timeout and received %s" % (
                        eol.__repr__(), response.__repr__()))
                return response
            else:
                response.extend(ans)
            sleep(MIN_TIMEOUT)
            if ans not in eol:
                continue
            if response[-leneol:] == eol:
                return response
        return response

    @property
    def in_waiting(self) -> int:
        length = 0
        sockets = select.select([self], [], [], 0.01)
        if sockets[0]:
            server: socket.socket = sockets[0][0] # type: ignore
            length = len(server.recv(self.chunk_size, socket.MSG_PEEK))
        if not length:
            self.validate_connection_by_last_time_packet()
        return length

    @property
    def out_waiting(self) -> int:
        return 0

    def reset_input_buffer(self) -> None:
        if self.in_waiting:
            self.read(self.in_waiting)

    def reset_output_buffer(self) -> None:
        ...

    def open(self):
        if self.fileno() == -1:
            raise SocketClosedError("Can't open closed socket")
        try:
            self.connect(self.addr_port)
        except TimeoutError:
            raise ConnectionError("Server is unreachable")
        except OSError as e:
            if platform == "win32":
                if e.errno == 10056:
                    # normal state: if the socket is opened it throws 10056
                    pass
                else:
                    logger.debug(f"On trying to connect to {self} e")
                    raise e
            elif platform == "linux":
                if e.errno == 106:
                    # normal state: if the socket is opened it throws 10056
                    pass
                else:
                    logger.debug(f"On trying to connect to {self} e")
                    raise e
            else:
                raise SystemError("The platform is not supported")

    def close(self):
        super().close()

    def is_open(self):
        """As the socket can't be checked properly if it's connected
        return False, assuming that .open method can be called easily"""
        try:
            sent = super().send(b"A")
        except OSError as e:
            if e.errno in (10038, 10054):  # socket was closed
                return False
            raise e
        if sent:
            return True
        return False



    def is_closed(self):
        ...

    def __call__(self):
        return IPPort(addr_port=self.addr_port, read_timeout=self.read_timeout)


@dataclass
class WorkerProperty:
    """
    params:
        port_type: can be "serial" or "network"
        listener: any unique string that is needed to validate listeners of the port
        timeout: maximum time in seconds during which the port block
        name: for "serial" it is "COM1", ""COM13", etc. For "network" - "123.123.123.123:3455"

    """

    port_type: str
    name: str

    def __init__(self, port_type: str = PORT_TYPE, name: str = "", listener: str = "", baudrate: int = 19200): #TODO: stopbits etc.
        if port_type not in (SERIAL_PORT, NETWORK_PORT):
            raise ValueError(f"Invalid port type for PortProperty {port_type}")
        if port_type == SERIAL_PORT:
            if not re.match(r"COM\d{1,3}", name) and not name.startswith("/dev/"):
                raise ValueError(f"Invalid port name {name}")
            
            # if int(name.replace("COM", "")) not in range(0, 256):
            #     raise ValueError(f"Invalid port name {name}")

        self.port_type = port_type
        self.name = name
        self.listener = listener
        self.baudrate = baudrate


class PortsUsed:
    """
    Attrs:
        self._port: dict
        A dictionary that contains ports in the way
            {port_name: serial.Serial}
    """

    def __init__(self):
        self._ports = {
        }

    def add_port(self, worker_property: WorkerProperty):
        """If there is no port with the given worker_property.name - create a new one
        and add it to self._ports. Don't open it
        Sometime all devices that uses a port will stop polling. But the port
        will still be in the list in closed state. So it must be reusable."""
        if worker_property.name in self._ports:
            logger.debug(f"Port {worker_property.name} was already created")
            self._add_listener(worker_property)
            return
        if worker_property.port_type == SERIAL_PORT:
            if worker_property.name not in find_com_ports():
                logger.info(f"{worker_property.name} is not ready")
                return
            port = SerialPort(
                rtscts=False, dsrdtr=False, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS,
                baudrate=worker_property.baudrate, port=worker_property.name, stopbits=serial.STOPBITS_ONE, write_timeout=0)
            logger.info(f"new port is created for {worker_property}")
            sleep(0.05)
        elif worker_property.port_type == NETWORK_PORT:
            addr, port = worker_property.name.split(":")
            port = int(port)
            port = IPPort(addr_port=(addr, port))
        try:
            self._ports[worker_property.name] = {
                "port": port,
                "port_type": worker_property.port_type,
                "listeners": [],
                "lock": Lock()
            }
        except NameError as e:
            logger.exception(f"Unsupported port type worker_property.port_type")
            raise e
        self._add_listener(worker_property)
        logger.info(f"Port is prepared {WorkerProperty}")

    def close_port(self, port_name: str, dev_id):
        port_data = self._ports.get(port_name)
        if port_data is None:
            message = f"Can't close port with {port_name=} because there is no such port"
            logger.exception(message)
            raise KeyError(message)
        listeners: list = port_data["listeners"]
        try:
            listeners.pop(listeners.index(dev_id))
        except ValueError:
            logger.warning(f"{dev_id} was not among the {port_name} {listeners=}")
        except IndexError:
            logger.warning(f"Couldn't pop {dev_id} from list, {port_name} listeneres was empty")
        if not listeners:
            if port_data["port_type"] == SERIAL_PORT:
                port: serial.Serial = port_data["port"]
                if port.is_open:
                    port.close()
            if port_data["port_type"] == NETWORK_PORT:
                port: IPPort = port_data["port"]
                port.close()
            try:
                del self._ports[port_name]
            except Exception as e:
                logger.error(f"{e} on closing {port_name}")


    def get_handle(self, port_name: str, timeout: float) -> tuple[Port, Lock]:
        if port_name not in self._ports:
            raise KeyError(f"Port name is not found {port_name=}")
        self._open_port(port_name)
        port = self._ports[port_name]["port"]
        lock = self._ports[port_name]["lock"]
        try:
            timeout = float(timeout)
        except ValueError:
            timeout = 0.35
        port.apply_settings({"timeout": timeout})
        if not port.is_open:
            port.open()
        return port, lock

    def list_active_ports(self):
        return list(self._ports.keys())

    def _add_listener(self, worker_property: WorkerProperty):
        if worker_property.listener in self._ports[worker_property.name]["listeners"]:
            return
        self._ports[worker_property.name]["listeners"].append(worker_property.listener)
        logger.info(f"New listener {worker_property.listener} is added to {self._ports[worker_property.name]}")

    def _open_port(self, port_name: str):
        """Prepare the port to write and read data.
        If throws serial.SerialException - handle it yourself"""
        port_data = self._ports.get(port_name)
        if port_data is None:
            message = f"Can't open port with {port_name=}"
            logger.error(message)
            raise KeyError(message)
        if port_data["port_type"] == SERIAL_PORT:
            port: serial.Serial = port_data["port"]
            if not port.is_open:
                port.open()
        elif port_data["port_type"] == NETWORK_PORT:
            port: IPPort = port_data["port"]
            try:
                port.open()
            except (SocketClosedError, OSError) as e:
                logger.error(f"{e} on open {port}")
                port_data["port"] = port()
                port = port_data["port"]
                port.open()
                

    def recreate_port(self, port_name):
        self._ports[port_name]["port"] = self._ports[port_name]["port"]()


def listen_port(dev_id: str, 
                timeout: float, 
                length: int|None, 
                request: bytes, 
                port_name: str,
                read_until=None) -> bytearray|bytes:
    
    port, lock = get_port(port_name, timeout)
    with lock:
        logger.debug(f"Lock of port is acquire by {dev_id} {port} ")
        try:
            if request:
                buffered_bytes = port.in_waiting
                if buffered_bytes:
                    data = port.read(buffered_bytes)
                    logger.debug(f"On {port} unexpected data was received and not processed, packet_length={len(data)}")
                    logger.debug(f"{data.hex()}")
                port.reset_output_buffer()
                if buffered_bytes:
                    port.reset_input_buffer()
            attempt = 0
            logger.debug(f"{request.__repr__()} to {dev_id} will be sent on {port}")
            ans = ser_request(request, attempt, port, length=length, read_until=read_until)  
        except (serial.SerialException, ) as e:
            if "ClearCommError" in str(e) or "FileNotFound" in str(e) or "Input/output error" in str(e):
                CONNECTOR.recreate_port(port_name)
            logger.debug(e)
            raise e
        except ConnectionError as e:
            logger.info(e)
            sleep(DEFAULT_TIMEOUT)
            CONNECTOR.recreate_port(port_name)
            raise e
        except Exception as e:
            logger.debug(e)
            raise e
        finally:
            logger.debug(F"lock of port is released de {dev_id} {port}")
    
  

    return ans


def get_port(port_name: str, timeout: float) -> tuple[Port, Lock]:
    port, lock = CONNECTOR.get_handle(port_name, timeout)
    return port, lock


def ser_request(request: bytearray|bytes, attempt: int, port: Port, length=None, read_until: bytes|None=None) -> bytes:
    """If length is not None - read given amount of bytes
    if length is None, but read_until is not None - read until given bytes"""
    try:
        # if request:
        port.write(request)
        if length is None:
            if read_until is not None:
                ser_ans = port.read_until(read_until)
            else:
                timeout = port.read_timeout
                ans = bytearray()
                init_time = time.time()
                end_time = init_time + float(timeout)
                while True:
                    try:
                        if not port.in_waiting:
                            if ans: # answer was recieved completely
                                break
                            continue
                        ans.extend(port.read(port.in_waiting))
                    finally:
                        sleep(MIN_TIMEOUT)
                        if time.time() > end_time:
                            break
                ser_ans = bytes(ans)
        else:
            ser_ans = port.read(length)
        # make sure there is no trailing data, e.g. in passive reading
        # if so - clear the buffer
        trailing_data_count = port.in_waiting
        if trailing_data_count:
            trailing_data = port.read(trailing_data_count)
            logger.debug(f"On request '{request.hex()}' unexpected data after the expected was received: {trailing_data.hex()}. It wasn't saved to DB")
        sleep(0.1)
        if ser_ans is None:
            ser_ans = b""
        return ser_ans
    except SocketClosedError as e:
        raise ConnectionError(f"{request.hex()=} connection error" )


def find_com_ports() -> list:
    from serial.tools import list_ports
    ports = list_ports.comports()
    logger.debug(f'Found ports {ports}')
    available_ports = []
    available_ports.extend(CONNECTOR.list_active_ports())

    for port in ports:
        logger.debug(f"{port.device=}{available_ports=}")
        if port.device in available_ports:
            continue
        try:
            uart = serial.Serial(port=port.device, rtscts=False, dsrdtr=False)   
            logger.debug(f"Trying to open port {port}")
            if uart.is_open:
                sleep(0.2)
                uart.close()
            available_ports.append(port.device)
        except serial.serialutil.SerialException:
            continue
        except Exception as e:
            logger.error(e)

    ports = sorted(set([i for i in available_ports]))

    return ports


def change_netw_addr_n_crc(request: str, netw_addr: int) -> str:
    """Convert request to one with correct network address
    and CRC. netw_addr must be in range(0, 256)"""

    netw_addr_hex = bytearray(int.to_bytes(netw_addr, 1, "big"))

    request_body = bytearray.fromhex(request[2:-4])
    netw_addr_hex.extend(request_body)
    request_body = netw_addr_hex
    crc = get_crc_bytes(request_body)
    request_body.extend(crc)
    request = request_body.hex()
    return request


def get_crc(response: bytes) -> int:
    """ if crc in response is correct return 0, else crc int"""
    crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
    return crc16(response)
    


def get_crc_bytes(bl: bytes) -> bytes:
    """return reversed crc16 modbus"""
    crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
    crc = crc16(bl)
    crc = hex(crc).replace("0x", "")
    missing_zeroes = "0" * (4 - len(crc))
    crc = missing_zeroes + crc
    return bytes.fromhex(crc[2:]) + bytes.fromhex(crc[:2])


def is_crc_correct(bl: bytearray):
    if get_crc(bl):
        return False
    return True

CONNECTOR = PortsUsed()