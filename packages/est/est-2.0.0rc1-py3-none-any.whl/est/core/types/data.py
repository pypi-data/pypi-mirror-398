from enum import Enum


class InputType(Enum):
    ascii_spectrum = "ascii"  # single or multi scan, single spectrum
    hdf5_spectra = "hdf5"  # multi scan, multi spectra
