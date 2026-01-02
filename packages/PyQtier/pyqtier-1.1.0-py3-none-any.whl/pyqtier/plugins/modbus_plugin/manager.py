from typing import Union, List
from ..plugins import PyQtierPlugin
from .models.modbus_model import ModbusModel

BAUDRATES_LIST = ["9600", "19200", "38400", "57600", "115200"]


class ModbusPluginManager(PyQtierPlugin):
    def __init__(self, with_baudrate: bool = True, default_baudrate: int = 9600, default_slave_id: int = 1, custom_ui=None):
        super().__init__()

        if with_baudrate:
            from .views.modbus_control_with_baudrate import Ui_ModbusWidget
            self._default_baudrate = default_baudrate
        else:
            from .views.modbus_control import Ui_ModbusWidget
            self._default_baudrate = 0

        self._with_baudrate = with_baudrate
        self._default_slave_id = default_slave_id

        if custom_ui:
            self._ui = custom_ui()
        else:
            self._ui = Ui_ModbusWidget()
        self._modbus = ModbusModel()

    def setup_view(self, *args, **kwargs):
        super().setup_view(*args, **kwargs)

        # Підписка на оновлення списку пристроїв
        self._modbus.devices_list_updated.connect(self._update_ports_list)
        self._update_ports_list()

        # Налаштування baudrate
        if self._with_baudrate:
            self._ui.cb_list_baudrates.addItems(BAUDRATES_LIST)
            self._ui.cb_list_baudrates.setCurrentIndex(BAUDRATES_LIST.index(str(self._default_baudrate)))

        # Налаштування slave_id
        self._ui.lineedit_slave_id.setText(str(self._default_slave_id))

        # Підписка на внутрішні сигнали
        self._modbus.connected.connect(self._on_connected)
        self._modbus.disconnected.connect(self._on_disconnected)
        self._modbus.connection_lost.connect(self._on_connection_lost)

        self.create_behavior()

    def create_behavior(self):
        self._ui.bt_connect_disconnect.clicked.connect(self._connect_disconnect_callback)

    # ===== УНІВЕРСАЛЬНІ МЕТОДИ =====

    def read(self, function_code: int, address: int, count: int = 1, slave_id: int = None) -> Union[
        List[int], List[bool], None]:
        """Універсальний метод читання"""
        if slave_id is None:
            slave_id = self._get_slave_id()
        return self._modbus.read(slave_id, function_code, address, count)

    def write(self, function_code: int, address: int, value: Union[int, bool, List[int], List[bool]],
              slave_id: int = None) -> bool:
        """Універсальний метод запису"""
        if slave_id is None:
            slave_id = self._get_slave_id()
        return self._modbus.write(slave_id, function_code, address, value)

    # ===== МЕТОДИ ЧИТАННЯ =====

    def read_holding_registers(self, address: int, count: int = 1, slave_id: int = None) -> Union[List[int], None]:
        if slave_id is None:
            slave_id = self._get_slave_id()
        return self._modbus.read_holding_registers(slave_id, address, count)

    def read_input_registers(self, address: int, count: int = 1, slave_id: int = None) -> Union[List[int], None]:
        if slave_id is None:
            slave_id = self._get_slave_id()
        return self._modbus.read_input_registers(slave_id, address, count)

    def read_coils(self, address: int, count: int = 1, slave_id: int = None) -> Union[List[bool], None]:
        if slave_id is None:
            slave_id = self._get_slave_id()
        return self._modbus.read_coils(slave_id, address, count)

    def read_discrete_inputs(self, address: int, count: int = 1, slave_id: int = None) -> Union[List[bool], None]:
        if slave_id is None:
            slave_id = self._get_slave_id()
        return self._modbus.read_discrete_inputs(slave_id, address, count)

    # ===== МЕТОДИ ЗАПИСУ =====

    def write_register(self, address: int, value: int, slave_id: int = None) -> bool:
        if slave_id is None:
            slave_id = self._get_slave_id()
        return self._modbus.write_single_register(slave_id, address, value)

    def write_registers(self, address: int, values: List[int], slave_id: int = None) -> bool:
        if slave_id is None:
            slave_id = self._get_slave_id()
        return self._modbus.write_multiple_registers(slave_id, address, values)

    def write_coil(self, address: int, value: bool, slave_id: int = None) -> bool:
        if slave_id is None:
            slave_id = self._get_slave_id()
        return self._modbus.write_single_coil(slave_id, address, value)

    def write_coils(self, address: int, values: List[bool], slave_id: int = None) -> bool:
        if slave_id is None:
            slave_id = self._get_slave_id()
        return self._modbus.write_multiple_coils(slave_id, address, values)

    # ===== ВНУТРІШНІ МЕТОДИ =====

    def _get_slave_id(self) -> int:
        """Отримати slave_id з LineEdit з валідацією"""
        try:
            text = self._ui.lineedit_slave_id.text()
            if not text:
                return self._default_slave_id
            slave_id = int(text)
            if 1 <= slave_id <= 247:
                return slave_id
            else:
                return self._default_slave_id
        except ValueError:
            return self._default_slave_id

    def _connect(self):
        port = self._ui.cb_serial_ports.currentText()
        if not port:
            if self._statusbar:
                self._statusbar.showMessage("Modbus: No port selected!", 4000)
            return

        self._modbus.set_serial_port(port)

        if self._with_baudrate:
            baudrate = int(self._ui.cb_list_baudrates.currentText())
            self._modbus.set_baudrate(baudrate)

        self._modbus.connect()

    def _disconnect(self):
        self._modbus.disconnect()

    def _connect_disconnect_callback(self):
        if self._modbus.is_connected:
            self._disconnect()
        else:
            self._connect()

    def _update_ports_list(self):
        current_port = self._ui.cb_serial_ports.currentText()
        available_ports = self._modbus.get_available_ports()

        self._ui.cb_serial_ports.clear()
        self._ui.cb_serial_ports.addItems(available_ports)

        if current_port in available_ports:
            self._ui.cb_serial_ports.setCurrentIndex(available_ports.index(current_port))

    def _on_connected(self):
        self._ui.bt_connect_disconnect.setText("Disconnect")
        if self._statusbar:
            port = self._modbus._port
            baudrate_info = f" @ {self._modbus._baudrate} baud" if self._with_baudrate else ""
            self._statusbar.showMessage(f"Modbus: Connected to {port}{baudrate_info}", 4000)

    def _on_disconnected(self):
        self._ui.bt_connect_disconnect.setText("Connect")
        if self._statusbar:
            self._statusbar.showMessage("Modbus: Disconnected", 4000)

    def _on_connection_lost(self):
        self._ui.bt_connect_disconnect.setText("Connect")
        if self._statusbar:
            self._statusbar.showMessage("Modbus: Connection lost!", 4000)

    # ===== ІНФОРМАЦІЯ =====

    @staticmethod
    def get_available_ports() -> List[str]:
        return ModbusModel.get_available_ports()

    def get_slave_id(self) -> int:
        return self._get_slave_id()

    # ===== ДОСТУП ДО СИГНАЛІВ =====

    @property
    def connected(self):
        return self._modbus.connected

    @property
    def disconnected(self):
        return self._modbus.disconnected

    @property
    def error_occurred(self):
        return self._modbus.error_occurred

    @property
    def connection_lost(self):
        return self._modbus.connection_lost

    @property
    def devices_list_updated(self):
        return self._modbus.devices_list_updated

    @property
    def data_ready(self):
        return self._modbus.data_ready
