from typing import Optional

from silx.io.url import DataUrl

from ..types.dimensions import DimensionsType
from ..types.dimensions import parse_dimensions
from ..units import as_energy_unit
from ..units import ur


class InputInformation:
    """
    Utility class to store information to generate XASObject
    """

    def __init__(
        self,
        spectra_url: Optional[None] = None,  # mu (numerator)
        channel_url: Optional[None] = None,  # energy
        dimensions: Optional[DimensionsType] = None,
        energy_unit=ur.eV,  # units of channel_url
        mu_ref_url: Optional[None] = None,  # mu (denominator)
        min_log: bool = False,  # -ln(numerator/denominator)
        is_concatenated: bool = False,
        trim_concatenated_n_points: int = 0,
        skip_concatenated_n_spectra: int = 0,
        concatenated_spectra_section_size: int = 0,
    ):
        self.spectra_url = spectra_url
        self.channel_url = channel_url
        self.dimensions = parse_dimensions(dimensions)
        self.energy_unit = energy_unit

        self.mu_ref_url = mu_ref_url
        self.min_log = min_log

        self.is_concatenated = is_concatenated
        self.trim_concatenated_n_points = trim_concatenated_n_points
        self.skip_concatenated_n_spectra = skip_concatenated_n_spectra
        self.concatenated_spectra_section_size = concatenated_spectra_section_size

    def to_dict(self) -> dict:
        def dump_url(url):
            if url in (None, ""):
                return None
            else:
                return url.path()

        return {
            "spectra_url": dump_url(self.spectra_url),
            "channel_url": dump_url(self.channel_url),
            "dimensions": self.dimensions,
            "energy_unit": str(self.energy_unit),
            "mu_ref_url": dump_url(self.mu_ref_url),
            "min_log": self.min_log,
            "is_concatenated": self.is_concatenated,
            "trim_concatenated_n_points": self.trim_concatenated_n_points,
            "skip_concatenated_n_spectra": self.skip_concatenated_n_spectra,
            "concatenated_spectra_section_size": self.concatenated_spectra_section_size,
        }

    @staticmethod
    def from_dict(ddict: dict):
        def load_url(url_name: str):
            url = ddict.get(url_name, None)

            if url in (None, ""):
                return None
            else:
                return DataUrl(path=url)

        return InputInformation(
            spectra_url=load_url("spectra_url"),
            channel_url=load_url("channel_url"),
            dimensions=ddict.get("dimensions", None),
            energy_unit=as_energy_unit(ddict.get("energy_unit", None)),
            mu_ref_url=load_url("mu_ref_url"),
            min_log=ddict.get("min_log", False),
            is_concatenated=ddict.get("is_concatenated", False),
            trim_concatenated_n_points=ddict.get("trim_concatenated_n_points", 0),
            skip_concatenated_n_spectra=ddict.get("skip_concatenated_n_spectra", 0),
            concatenated_spectra_section_size=ddict.get(
                "concatenated_spectra_section_size", 0
            ),
        )
