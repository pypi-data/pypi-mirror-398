"""
This module is used to manage the rsync between files for transfert.
"""

from AnyQt.QtCore import QEvent
from AnyQt.QtCore import Qt
from AnyQt.QtCore import QUrl
from AnyQt.QtCore import pyqtSignal as Signal
from AnyQt.QtWidgets import QApplication

from ..core.utils.designpattern import singleton

# TODO: this should be removed


@singleton
class QApplicationManager(QApplication):
    """Return a singleton on the CanvasApplication"""

    fileOpenRequest = Signal(QUrl)

    def __init__(self):
        QApplication.__init__(self, [])
        self.setAttribute(Qt.AA_DontShowIconsInMenus, True)

    def event(self, event):
        if event.type() == QEvent.FileOpen:
            self.fileOpenRequest.emit(event.url())

        return QApplication.event(self, event)
