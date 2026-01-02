from typing import Callable, Optional

from .auxiliary import *
from .models.data_processor import UsbDataProcessor
from .models.serial_model import SerialModel, Statuses
from ..plugins import PyQtierPlugin


class UsbPluginManager(PyQtierPlugin):
    def __init__(self, with_baudrate: bool = False, default_baudrate: int = 9600, custom_ui=None):
        super().__init__()

        if with_baudrate:
            from .views.usb_control_with_baudrate import Ui_UsbWidget
            self._default_baudrate: int = default_baudrate
        else:
            from .views.usb_control import Ui_UsbWidget
            self._default_baudrate: int = 0

        self._with_baudrate: bool = with_baudrate

        if custom_ui:
            self._ui = custom_ui()
        else:
            self._ui = Ui_UsbWidget()

        self._serial: SerialModel = SerialModel()

        self._external_lost_connection_callback: Optional[Callable] = None

    def setup_view(self, *args, **kwargs):
        super().setup_view(*args, **kwargs)
        self._serial.devices_list_updated.connect(self._cb_list_usb_devices_callback)
        self._cb_list_usb_devices_callback()

        if self._with_baudrate:
            self._ui.cb_list_baud_rates.addItems(BAUDRATES_LIST)
            self._ui.cb_list_baud_rates.setCurrentIndex(BAUDRATES_LIST.index(str(self._default_baudrate)))

        self.create_behavior()

    def create_behavior(self):
        self._ui.bt_connect_disconnect.clicked.connect(self._connect_disconnect_callback)

    def send_data(self, data: dict):
        self._serial.write(data)

    # ===== SETTERS =====
    def set_obtain_data_callback(self, callback):
        self._serial.set_data_ready_callback(callback)

    def set_error_callback(self, callback):
        self._serial.set_error_callback(callback)

    def set_connection_lost_callback(self, callback):
        self._external_lost_connection_callback = callback
        self._serial.set_connection_lost_callback(self._lost_connection_callback)

    def set_connect_callback(self, callback: Callable):
        self._serial.set_connect_callback(callback)

    def set_disconnect_callback(self, callback: Callable):
        self._serial.set_disconnect_callback(callback)

    def set_data_processor(self, data_processor: UsbDataProcessor):
        self._serial.set_data_processor(data_processor)

    # ===== INTERNAL METHODS =====
    def _connect(self):
        # Connecting
        self._serial.set_serial_port(self._ui.cb_list_usb_devices.currentText().split(" - ")[0])
        # Setting baud rate if it enabled
        if self._with_baudrate:
            self._serial.set_baud_rate(int(self._ui.cb_list_baud_rates.currentText()))

        # Checking if connecting successfully
        if self._serial.connect() == Statuses.OK:
            # self.bt_com.setIcon(self.__icon_com_disconnect)
            self._ui.bt_connect_disconnect.setText("Disconnect")
            if self._statusbar:
                self._show_status_message(f"{self._ui.cb_list_usb_devices.currentText()} connected!")

        else:
            if self._statusbar:
                self._show_status_message(f"{self._ui.cb_list_usb_devices.currentText()} connection failure!")
            # Updating list of device if connecting failure
            self._cb_list_usb_devices_callback()

    def _disconnect(self):
        if self._serial.is_connected:
            self._serial.disconnect()

        # self.bt_com.setIcon(self.__icon_com_connect)
        self._ui.bt_connect_disconnect.setText("Connect")

        if self._statusbar:
            self._show_status_message(f"{self._ui.cb_list_usb_devices.currentText()} disconnected!")

    def _connect_disconnect_callback(self):
        if self._serial.is_connected:
            self._disconnect()
        else:
            self._connect()

    def _cb_list_usb_devices_callback(self):
        current_device = self._ui.cb_list_usb_devices.currentText()
        available_devices = self._serial.get_available_ports()
        self._ui.cb_list_usb_devices.clear()
        self._ui.cb_list_usb_devices.addItems(available_devices)
        if current_device in available_devices:
            self._ui.cb_list_usb_devices.setCurrentIndex(available_devices.index(current_device))

    def _show_status_message(self, message):
        self._statusbar.showMessage(message, 4000)

    def _lost_connection_callback(self):
        self._disconnect()
        self._show_status_message("Connection lost!")

        if self._external_lost_connection_callback:
            self._external_lost_connection_callback()
