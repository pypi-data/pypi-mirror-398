"""Physical units for engineering and science"""

from typing import Union

import pint

#: unit registry
ur = pint.get_application_registry()


def as_energy_unit(unit: Union[str, ur.Unit]) -> ur.Unit:
    if isinstance(unit, str):
        lunit = unit.lower()
        if lunit in ("ev", "electron_volt"):
            return ur.eV
        elif lunit in ("kev", "kiloelectron_volt", "kilo_electron_volt"):
            return ur.keV
        elif lunit == ("j", "joule"):
            return ur.J
        elif lunit == ("kj", "kilojoule", "kilo_joule"):
            return ur.kJ
        unit = ur.Unit(unit)
    if not isinstance(unit, ur.Unit):
        raise ValueError(f"`{unit}` is not a valid unit")
    if not unit.is_compatible_with("eV"):
        raise ValueError(f"`{unit}` is not a valid energy unit")
    return unit
