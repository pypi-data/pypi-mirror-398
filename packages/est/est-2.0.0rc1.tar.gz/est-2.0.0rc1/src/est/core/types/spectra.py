import logging
from typing import Iterable
from typing import Iterator
from typing import Tuple
from typing import Union

import numpy

from .dimensions import transform_to_standard
from .spectrum import Spectrum

_logger = logging.getLogger(__name__)


class Spectra:
    """
    A map of spectrum.

    - data: numpy array of Spectrum. Expected to be 2D.
    - energy: set of energy for each position (x,y)
    """

    def __init__(
        self, energy, spectra: Union[Iterable[Spectrum], numpy.ndarray, None] = None
    ):
        self.__data = numpy.array([], dtype=object)
        self.energy = energy

        if spectra is None:
            spectra = []

        if not isinstance(spectra, (list, tuple, numpy.ndarray)):
            raise TypeError(f"Invalid spectra type: {type(spectra)}")

        spectrum_list = []
        if isinstance(spectra, numpy.ndarray):
            if spectra.ndim == 2:
                # 2D ndarray of Spectrum instances
                for spectrum in spectra.flat:
                    if not isinstance(spectrum, Spectrum):
                        raise TypeError(
                            "2D spectra array must contain Spectrum objects"
                        )
                self.__data = spectra.astype(object)
            else:
                # 3D ndarray of numbers
                if spectra.ndim != 3:
                    raise ValueError("Spectra ndarray must be 2D or 3D")

                # spectra dims: energy, y, x
                for y in range(spectra.shape[1]):
                    for x in range(spectra.shape[2]):
                        spectrum_list.append(
                            Spectrum(
                                energy=self.energy,
                                mu=spectra[:, y, x],
                            )
                        )

                shape = spectra.shape[-2:]
                self.__data = numpy.array(spectrum_list, dtype=object).reshape(shape)
        else:
            # 1D sequence of Spectrum instances
            for spectrum in spectra:
                if not isinstance(spectrum, Spectrum):
                    raise TypeError("spectra must contain Spectrum objects only")
                spectrum_list.append(spectrum)

            shape = (1, -1)
            self.__data = numpy.array(spectrum_list, dtype=object).reshape(shape)

    def check_validity(self):
        for spectrum in self.data.flat:
            if not isinstance(spectrum, Spectrum):
                raise TypeError("spectra must contain Spectrum objects")
            if not isinstance(
                spectrum.energy,
                numpy.ndarray,
            ):
                raise ValueError("Spectrum.energy must be numpy array")
            if spectrum.mu is not None and not isinstance(spectrum.mu, numpy.ndarray):
                raise ValueError("Spectrum.mu must be numpy array")

    @property
    def data(self) -> numpy.ndarray:
        return self.__data

    def __getitem__(self, item) -> Spectrum:
        return self.__data[item]

    def __iter__(self) -> Iterator[Spectrum]:
        return iter(self.data.flat)

    @property
    def shape(self) -> Tuple[int, ...]:
        return self.__data.shape

    def reshape(self, shape: Tuple[int, int]) -> None:
        if len(shape) != 2 or None in shape:
            raise ValueError("shape must be a 2-tuple of ints")
        self.__data = self.__data.reshape(shape)

    @property
    def energy(self) -> numpy.ndarray:
        """Energy in eV"""
        return self.__energy

    @energy.setter
    def energy(self, energy: numpy.ndarray):
        self.__energy = energy
        if self.data.size > 0:
            first = self.data.flat[0]
            if first.energy is not None and len(first.energy) != len(energy):
                _logger.warning("Spectra and energy have incompatible dimensions")

    def as_ndarray(self, path: str) -> numpy.ndarray:
        """Extract value from each Spectrum and return as a 2D or 3D array."""
        if self.data.size == 0:
            return None

        values = []
        for spectrum in self.data.flat:
            try:
                value = spectrum.get_value(path)
            except AttributeError:
                _logger.info("Failed to access %r", path)
                return None
            if value is None:
                return None
            values.append(value)

        if not values:
            return None

        array = numpy.stack(values, axis=-1)

        shape = list(self.data.shape)
        shape.insert(0, array.shape[0])
        return array.reshape(shape)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Spectra):
            return False
        if self.data.shape != other.data.shape:
            return False
        return all(
            s1.model_dump() == s2.model_dump()
            for s1, s2 in zip(self.data.flat, other.data.flat)
        )

    @classmethod
    def from_dict(cls, data, dimensions):
        from ..io._utils.load import load_data  # avoid cyclic import

        if isinstance(data, str):
            spectra = load_data(data_url=data)
            return transform_to_standard(spectra, dimensions)

        if isinstance(data, Iterable):
            spectra = [Spectrum.model_validate(d) for d in data]
            return cls(energy=spectra[0].energy, spectra=spectra)

        raise TypeError(f"Unhandled input type: {type(data)}")
