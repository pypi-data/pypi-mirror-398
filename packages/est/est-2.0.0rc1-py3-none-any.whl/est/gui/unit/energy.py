"""Tools to select energy unit"""

from silx.gui import qt

from ...core.units import ur


class EnergyUnitSelector(qt.QComboBox):
    """Simple class to define a unit for energy"""

    def __init__(self, parent=None):
        qt.QComboBox.__init__(self, parent)
        for unit in ("eV", "keV", "J", "kJ"):
            self.addItem(unit)

    def getUnit(self):
        current_unit = self.currentText()
        if current_unit == "eV":
            return ur.eV
        elif current_unit == "keV":
            return ur.keV
        elif current_unit == "J":
            return ur.J
        elif current_unit == "kJ":
            return ur.kJ
        else:
            raise ValueError("current unit is not supported")

    def setUnit(self, unit: str) -> None:
        if unit in ("eV", "keV", "J", "kJ"):
            txt = unit
        elif unit == ur.eV:
            txt = "eV"
        elif unit == ur.keV:
            txt = "keV"
        elif unit == ur.J:
            txt = "J"
        elif unit == ur.kJ:
            txt = "kJ"
        else:
            raise ValueError("Given unit is not managed: {}".format(unit))

        index = self.findText(txt)
        if index >= 0:
            self.setCurrentIndex(index)
