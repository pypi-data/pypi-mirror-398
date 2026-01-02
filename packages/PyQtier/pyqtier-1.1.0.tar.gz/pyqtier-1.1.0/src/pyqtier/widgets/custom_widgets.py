from typing import Callable

from PyQt5 import QtCore, QtWidgets


class ExtendedComboBox(QtWidgets.QComboBox):
    """
    ComboBox with auto-updating data list.
    To enable updates, you need to set a callback
    using the set_refresh_callback(<callback>) method.
    When clicking on the ComboBox, the data list
    will be updated before opening.
    """

    popupAboutToBeShown = QtCore.pyqtSignal()

    def __init__(self, *args):
        super(ExtendedComboBox, self).__init__(*args)
        self.__refresh_callback = None

    def set_refresh_callback(self, update_callback: Callable):
        """
        Set a callback for updating the list of items that will be called
        before showing the items when opening the ComboBox.
        :param update_callback: Callback function that will perform the data update in ComboBox
        :return: None
        """
        if callable(update_callback):
            self.__refresh_callback = update_callback

    def showPopup(self):
        """
        Method that renders items when opening the ComboBox.
        The RefreshCallback is called before calling the main method
        :return: None
        """
        if self.__refresh_callback:
            self.__refresh_callback()
        self.popupAboutToBeShown.emit()
        super(ExtendedComboBox, self).showPopup()
