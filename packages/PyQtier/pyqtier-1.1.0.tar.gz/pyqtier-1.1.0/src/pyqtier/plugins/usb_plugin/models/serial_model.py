from enum import Enum, auto
from typing import Callable, Optional

import serial
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from serial.tools import list_ports

from .data_processor import UsbDataProcessor

DELAY_BETWEEN_READING = 1  # msec
CONNECTION_CHECK_INTERVAL = 500  # msec
DEVICE_LIST_UPDATE_INTERVAL = 1000  # msec


class Statuses(Enum):
    OK = auto()
    ERROR = auto()
    STATUS_ERROR_CONNECTION_TIMEOUT = auto()
    DATA_PROCESSOR_DID_NOT_SET = auto()
    DEVICE_DISCONNECTED = auto()


class SerialModel(QThread):
    raw_data_received = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)
    data_ready = pyqtSignal(dict)
    connection_lost = pyqtSignal()
    connect_signal = pyqtSignal()
    disconnect_signal = pyqtSignal()
    devices_list_updated = pyqtSignal(list)  # New signal for device list updates

    def __init__(self):
        super().__init__()
        self._baud_rate = 0
        self._is_connection_via_usb = False
        self._serial_port = "COM1"
        self._ser = None
        self._is_serial_connected = False
        self.data_processor: Optional[UsbDataProcessor] = None

        # Connection monitoring timer
        self._connection_timer = QTimer(self)
        self._connection_timer.timeout.connect(self._check_connection)

        # Device list update timer
        self._device_list_timer = QTimer(self)
        self._device_list_timer.timeout.connect(self._update_device_list)

        # Keep track of last known devices
        self._last_known_devices = set()

        self.start_monitoring_devices_list()

    def start_monitoring(self):
        """Start connection monitoring and device list updating"""
        self._connection_timer.start(CONNECTION_CHECK_INTERVAL)

    def start_monitoring_devices_list(self):
        self._device_list_timer.start(DEVICE_LIST_UPDATE_INTERVAL)

    def stop_monitoring(self):
        """Stop connection monitoring and device list updating"""
        self._connection_timer.stop()

    def stop_monitoring_devices_list(self):
        self._device_list_timer.stop()

    def _check_connection(self):
        """Check if the current connection is still valid"""
        if self._is_serial_connected and self._ser:
            try:
                # Check if the port is still available
                if self._serial_port not in [p.device for p in list_ports.comports()]:
                    self._handle_connection_loss()
                    return
            except (serial.SerialException, IOError):
                self._handle_connection_loss()

    def _handle_connection_loss(self):
        """Handle connection loss events"""
        self._is_serial_connected = False
        self.error_occurred.emit("Connection lost")
        self.connection_lost.emit()
        self.disconnect()

    def _update_device_list(self):
        """Update the list of available devices and emit if changed"""
        current_devices = set(self.get_available_ports())
        if current_devices != self._last_known_devices:
            self._last_known_devices = current_devices
            self.devices_list_updated.emit(list(current_devices))

    # ===== SETTINGS SERIAL PORTS =====
    def set_connection_type(self, is_connection_via_usb: bool):
        self._is_connection_via_usb = is_connection_via_usb

    def set_serial_port(self, serial_port: str):
        """
        Setter of Serial port.
        :param serial_port: str name of Serial ports
        """
        self._serial_port = serial_port

    def set_baud_rate(self, br: int = 115200):
        """
        Method for setting baud rate
        :param br: can be 9600 - 115200 (default value)
        """
        self._baud_rate = br

    # ===== SETTINGS CALLBACKS =====
    def set_data_processor(self, data_processor: UsbDataProcessor):
        self.raw_data_received.connect(self._parsing)
        self.data_processor = data_processor

    def set_data_ready_callback(self, callback: Callable):
        self.data_ready.connect(callback)

    def set_error_callback(self, callback: Callable):
        self.error_occurred.connect(callback)

    def set_connection_lost_callback(self, callback: Callable):
        self.connection_lost.connect(callback)

    def set_connect_callback(self, callback: Callable):
        self.connect_signal.connect(callback)

    def set_disconnect_callback(self, callback: Callable):
        self.disconnect_signal.connect(callback)

    # ===== SERIAL PROCESSING =====
    def connect(self) -> Statuses:
        """
        Method which is connecting to Serial device.
        :return: Status of the connection attempt
        """
        try:
            self._ser = serial.Serial(self._serial_port, self._baud_rate)
            self.start()
            self.start_monitoring()  # Start monitoring when connected
        except serial.SerialException as err:
            self.error_occurred.emit(str(err))
            return Statuses.ERROR
        else:
            self._is_serial_connected = True
            self.connect_signal.emit()
            return Statuses.OK

    def disconnect(self) -> Statuses:
        """
        Method which is disconnecting from Serial device.
        :return: Status of the disconnection attempt
        """
        try:
            self._is_serial_connected = False
            self.stop_monitoring()  # Stop monitoring when disconnected
            self.wait()
            if self._ser and self._ser.is_open:
                self._ser.close()
            self.disconnect_signal.emit()
        except serial.SerialException as err:
            return Statuses.ERROR
        else:
            return Statuses.OK

    def write(self, data) -> Statuses:
        """
        Write data to serial port
        :param data:
        :return: Кількість надісланих байт
        """
        if self._is_serial_connected:
            try:
                if self.data_processor is not None:
                    serialized_data = self.data_processor.serialize(data)
                    return self._ser.write(serialized_data)
                else:
                    return Statuses.DATA_PARSER_DID_NOT_SET
            except serial.serialutil.SerialTimeoutException as err:
                # Якщо COM-порту не знайдено - розриваємо зв'язок
                self.error_occurred.emit(str(err))
                return Statuses.STATUS_ERROR_CONNECTION_TIMEOUT

    def run(self):
        try:
            while self.is_connected:
                if self._ser.in_waiting:
                    data = self._ser.read(self._ser.in_waiting)
                    self.raw_data_received.emit(data)
                self.msleep(DELAY_BETWEEN_READING)  # small delay for decrease load
        except Exception as err:
            self.error_occurred.emit(str(err))

    # ===== GETTERS =====
    @property
    def is_connected(self) -> bool:
        return self._is_serial_connected

    @staticmethod
    def get_available_ports(item_as_str: bool = True) -> list[str]:
        """
        Get available on system serial ports
        :param item_as_str: True if you need str name of serial ports, False if you need ListPortInfo
        :return: List of available serial ports
        """
        return [str(i) for i in list_ports.comports()] if item_as_str else list_ports.comports()

    # ===== INTERNAL METHODS =====
    def _parsing(self, data: bytes):
        parsed_data = self.data_processor.parse(data)
        if parsed_data:
            self.data_ready.emit(parsed_data)
