from enum import Enum, auto
from typing import Optional, List, Union
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from serial.tools import list_ports
from pymodbus.client import ModbusSerialClient


class Statuses(Enum):
    OK = auto()
    ERROR = auto()


class ModbusModel(QObject):
    # Сигнали
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    connection_lost = pyqtSignal()
    error_occurred = pyqtSignal(str)
    devices_list_updated = pyqtSignal(list)
    data_ready = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._client: Optional[ModbusSerialClient] = None
        self._port = "COM1"
        self._baudrate = 9600
        self._is_connected = False

        # Моніторинг портів
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_ports)
        self._timer.start(1000)
        self._last_ports = set()

    def set_serial_port(self, port: str):
        self._port = port

    def set_baudrate(self, baudrate: int):
        self._baudrate = baudrate

    def _emit_data(self, data: dict):
        self.data_ready.emit(data)

    def connect(self) -> Statuses:
        try:
            self._client = ModbusSerialClient(
                port=self._port,
                baudrate=self._baudrate,
                timeout=1
            )

            if self._client.connect():
                self._is_connected = True
                self.connected.emit()
                return Statuses.OK
            else:
                self.error_occurred.emit("Failed to connect")
                return Statuses.ERROR
        except Exception as e:
            self.error_occurred.emit(str(e))
            return Statuses.ERROR

    def disconnect(self):
        self._is_connected = False
        if self._client:
            self._client.close()
            self._client = None
        self.disconnected.emit()

    # ===== МЕТОДИ ЧИТАННЯ =====

    def read_coils(self, slave_id: int, address: int, count: int = 1) -> Optional[List[bool]]:
        """Читання Coils (FC=0x01)"""
        if not self._is_connected or not self._client:
            return None

        try:
            result = self._client.read_coils(address, count=count, device_id=slave_id)
            if result.isError():
                self.error_occurred.emit(f"Read coils error: {result}")
                return None
            return result.bits[:count]
        except Exception as e:
            self.error_occurred.emit(f"Read coils exception: {str(e)}")
            return None

    def read_discrete_inputs(self, slave_id: int, address: int, count: int = 1) -> Optional[List[bool]]:
        """Читання Discrete Inputs (FC=0x02)"""
        if not self._is_connected or not self._client:
            return None

        try:
            result = self._client.read_discrete_inputs(address, count=count, device_id=slave_id)
            if result.isError():
                self.error_occurred.emit(f"Read discrete inputs error: {result}")
                return None
            return result.bits[:count]
        except Exception as e:
            self.error_occurred.emit(f"Read discrete inputs exception: {str(e)}")
            return None

    def read_holding_registers(self, slave_id: int, address: int, count: int = 1) -> Optional[List[int]]:
        """Читання Holding Registers (FC=0x03)"""
        if not self._is_connected or not self._client:
            return None

        try:
            result = self._client.read_holding_registers(address, count=count, device_id=slave_id)
            if result.isError():
                self.error_occurred.emit(f"Read holding registers error: {result}")
                return None
            return result.registers
        except Exception as e:
            self.error_occurred.emit(f"Read holding registers exception: {str(e)}")
            return None

    def read_input_registers(self, slave_id: int, address: int, count: int = 1) -> Optional[List[int]]:
        """Читання Input Registers (FC=0x04)"""
        if not self._is_connected or not self._client:
            return None

        try:
            result = self._client.read_input_registers(address, count=count, device_id=slave_id)
            if result.isError():
                self.error_occurred.emit(f"Read input registers error: {result}")
                return None
            return result.registers
        except Exception as e:
            self.error_occurred.emit(f"Read input registers exception: {str(e)}")
            return None

    # ===== МЕТОДИ ЗАПИСУ =====

    def write_single_coil(self, slave_id: int, address: int, value: bool) -> bool:
        """Запис одного Coil (FC=0x05)"""
        if not self._is_connected or not self._client:
            return False

        try:
            result = self._client.write_coil(address, value, device_id=slave_id)
            if result.isError():
                self.error_occurred.emit(f"Write coil error: {result}")
                return False
            return True
        except Exception as e:
            self.error_occurred.emit(f"Write coil exception: {str(e)}")
            return False

    def write_single_register(self, slave_id: int, address: int, value: int) -> bool:
        """Запис одного регістру (FC=0x06)"""
        if not self._is_connected or not self._client:
            return False

        try:
            result = self._client.write_register(address, value, device_id=slave_id)
            if result.isError():
                self.error_occurred.emit(f"Write register error: {result}")
                return False
            return True
        except Exception as e:
            self.error_occurred.emit(f"Write register exception: {str(e)}")
            return False

    def write_multiple_coils(self, slave_id: int, address: int, values: List[bool]) -> bool:
        """Запис кількох Coils (FC=0x0F)"""
        if not self._is_connected or not self._client:
            return False

        try:
            result = self._client.write_coils(address, values, device_id=slave_id)
            if result.isError():
                self.error_occurred.emit(f"Write multiple coils error: {result}")
                return False
            return True
        except Exception as e:
            self.error_occurred.emit(f"Write multiple coils exception: {str(e)}")
            return False

    def write_multiple_registers(self, slave_id: int, address: int, values: List[int]) -> bool:
        """Запис кількох регістрів (FC=0x10)"""
        if not self._is_connected or not self._client:
            return False

        try:
            result = self._client.write_registers(address, values, device_id=slave_id)
            if result.isError():
                self.error_occurred.emit(f"Write multiple registers error: {result}")
                return False
            return True
        except Exception as e:
            self.error_occurred.emit(f"Write multiple registers exception: {str(e)}")
            return False

    # ===== УНІВЕРСАЛЬНІ МЕТОДИ =====

    def read(self, slave_id: int, function_code: int, address: int, count: int = 1) -> Union[
        List[int], List[bool], None]:
        """
        Універсальний метод читання

        :param slave_id: Адреса slave пристрою (1-247)
        :param function_code: Код функції:
            - 1: Read Coils
            - 2: Read Discrete Inputs
            - 3: Read Holding Registers
            - 4: Read Input Registers
        :param address: Адреса початку читання
        :param count: Кількість елементів для читання
        :return: Список значень або None
        """
        if function_code == 1:
            return self.read_coils(slave_id, address, count)
        elif function_code == 2:
            return self.read_discrete_inputs(slave_id, address, count)
        elif function_code == 3:
            return self.read_holding_registers(slave_id, address, count)
        elif function_code == 4:
            return self.read_input_registers(slave_id, address, count)
        else:
            self.error_occurred.emit(f"Unsupported read function code: {function_code}")
            return None

    def write(self, slave_id: int, function_code: int, address: int,
              value: Union[int, bool, List[int], List[bool]]) -> bool:
        """
        Універсальний метод запису

        :param slave_id: Адреса slave пристрою (1-247)
        :param function_code: Код функції:
            - 5: Write Single Coil
            - 6: Write Single Register
            - 15: Write Multiple Coils
            - 16: Write Multiple Registers
        :param address: Адреса запису
        :param value: Значення для запису (одне або список)
        :return: True при успіху
        """
        if function_code == 5:
            return self.write_single_coil(slave_id, address, value)
        elif function_code == 6:
            return self.write_single_register(slave_id, address, value)
        elif function_code == 15:
            return self.write_multiple_coils(slave_id, address, value)
        elif function_code == 16:
            return self.write_multiple_registers(slave_id, address, value)
        else:
            self.error_occurred.emit(f"Unsupported write function code: {function_code}")
            return False

    # ===== МОНІТОРИНГ =====

    def _check_ports(self):
        """Перевірка списку портів і з'єднання"""
        current_ports = set(self.get_available_ports())

        # Оновлення списку портів
        if current_ports != self._last_ports:
            self._last_ports = current_ports
            self.devices_list_updated.emit(list(current_ports))

        # Перевірка з'єднання
        if self._is_connected and self._port not in current_ports:
            self._is_connected = False
            self.connection_lost.emit()

    # ===== ВЛАСТИВОСТІ =====

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @staticmethod
    def get_available_ports() -> List[str]:
        return [p.device for p in list_ports.comports()]
