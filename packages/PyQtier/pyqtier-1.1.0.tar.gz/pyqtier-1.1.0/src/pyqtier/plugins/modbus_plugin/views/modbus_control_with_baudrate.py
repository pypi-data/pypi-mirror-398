# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWidgets


class Ui_ModbusWidget(object):
    def setupUi(self, ModbusWidget):
        ModbusWidget.setObjectName("ModbusWidget")
        ModbusWidget.resize(250, 50)

        self.horizontalLayout = QtWidgets.QHBoxLayout(ModbusWidget)
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.frame = QtWidgets.QFrame(ModbusWidget)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")

        self.gridLayout = QtWidgets.QGridLayout(self.frame)
        self.gridLayout.setObjectName("gridLayout")

        # Slave ID
        self.lineedit_slave_id = QtWidgets.QLineEdit(self.frame)
        self.lineedit_slave_id.setPlaceholderText("ID:")
        self.lineedit_slave_id.setObjectName("lineedit_slave_id")
        self.gridLayout.addWidget(self.lineedit_slave_id, 0, 0, 1, 1)

        # COM Port
        self.cb_serial_ports = QtWidgets.QComboBox(self.frame)
        self.cb_serial_ports.setObjectName("cb_serial_ports")
        self.gridLayout.addWidget(self.cb_serial_ports, 0, 1, 1, 1)

        # Baudrate
        self.cb_list_baudrates = QtWidgets.QComboBox(self.frame)
        self.cb_list_baudrates.setObjectName("cb_list_baudrates")
        self.gridLayout.addWidget(self.cb_list_baudrates, 0, 2, 1, 1)

        # Connect Button
        self.bt_connect_disconnect = QtWidgets.QPushButton(self.frame)
        self.bt_connect_disconnect.setObjectName("bt_connect_disconnect")
        self.gridLayout.addWidget(self.bt_connect_disconnect, 0, 3, 1, 1)

        self.horizontalLayout.addWidget(self.frame)

        self.retranslateUi(ModbusWidget)
        QtCore.QMetaObject.connectSlotsByName(ModbusWidget)

    def retranslateUi(self, ModbusWidget):
        _translate = QtCore.QCoreApplication.translate
        ModbusWidget.setWindowTitle(_translate("ModbusWidget", "Modbus"))
        self.bt_connect_disconnect.setText(_translate("ModbusWidget", "Connect"))
