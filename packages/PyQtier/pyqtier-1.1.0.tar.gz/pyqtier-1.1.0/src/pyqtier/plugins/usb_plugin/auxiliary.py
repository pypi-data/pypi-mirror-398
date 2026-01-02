BAUDRATES_LIST = ["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]
DEFAULT_BAUDRATE = 9600

THEME_SETTINGS = {
    "with_labels": True
}

HELP_TEXT = """For setting up current plugin you need to do a few steps:
1. Create your own data parser which inherits from UsbPluginManager or use UsbDataParser
    from pyqtier.plugins import UsbDataParser
    
    self.usb_data_parser = UsbDataParser()
    
2. Create a UsbPluginManager 
    self.usb_manager = UsbPluginManager(with_baudrate=True)

3. Setup view
    self.usb_manager.setup_view(self.main_window.ui.widget, self.main_window.ui.statusbar)

4. Set data parser:
    self.usb_manager.set_data_parser(self.usb_data_parser)  
    
5. Set callback which obtain processed data
    self.usb_manager.set_obtain_data_callback(self.test_usb_window.obtain_usb_data)

6. If you need sending data, you need use send function in usb_manager
    self.test_usb_window.set_send_callback(self.usb_manager.send)  
"""
