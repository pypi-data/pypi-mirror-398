"""module for giving information on process progress"""

import sys
from enum import Enum

try:
    # FIXME: stdout log should be optional and not activated when using Qt / Orange.
    # The different Process could have a `stdout_log` variable, true by default and
    # set to false by `EwoksOrange` widgets.
    from AnyQt.QtWidgets import QApplication
except ImportError:
    _IN_QT_APP = QApplication.instance() is not None
else:
    _IN_QT_APP = False


class _Advancement(Enum):
    step_1 = "\\"
    step_2 = "-"
    step_3 = "/"
    step_4 = "|"

    @staticmethod
    def getNextStep(step):
        if step is _Advancement.step_1:
            return _Advancement.step_2
        elif step is _Advancement.step_2:
            return _Advancement.step_3
        elif step is _Advancement.step_3:
            return _Advancement.step_4
        else:
            return _Advancement.step_1

    @staticmethod
    def getStep(value):
        if value % 4 == 0:
            return _Advancement.step_4
        elif value % 3 == 0:
            return _Advancement.step_3
        elif value % 2 == 0:
            return _Advancement.step_2
        else:
            return _Advancement.step_1


class Progress:
    """Simple interface for defining advancement on a 100 percentage base"""

    def __init__(self, name):
        self._name = name
        self.reset()

    def reset(self, max_=None):
        self._nProcessed = 0
        self._maxProcessed = max_

    def startProcess(self):
        self.setAdvancement(0)

    def setAdvancement(self, value):
        if not _IN_QT_APP:
            return
        length = 20  # modify this to change the length
        block = int(round(length * value / 100))
        msg = "\r{0}: [{1}] {2}%".format(
            self._name, "#" * block + "-" * (length - block), round(value, 2)
        )
        if value >= 100:
            msg += " DONE\r\n"
        sys.stdout.write(msg)
        sys.stdout.flush()

    def endProcess(self):
        self.setAdvancement(100)

    def setMaxSpectrum(self, n):
        self._maxProcessed = n

    def increaseAdvancement(self, i=1):
        self._nProcessed += i
        self.setAdvancement((self._nProcessed / self._maxProcessed) * 100)
