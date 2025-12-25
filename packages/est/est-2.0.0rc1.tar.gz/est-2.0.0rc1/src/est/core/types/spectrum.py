from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import get_args
from typing import get_origin

import numpy
from pydantic import BaseModel
from pydantic import Field
from pydantic.fields import FieldInfo


def SpectrumField(
    *,
    default=None,
    label: str = "",
    x: str = "",
    description: Optional[str] = None,
    **kwargs,
):
    """
    Domain-specific wrapper around pydantic.Field that attaches plotting metadata.

    :param default: default value.
    :param label: Axis label used for plotting.
    :param x: Name of the x-axis field.
    :param description: Human-readable description.
    """
    json_schema_extra: Dict[str, Any] = kwargs.pop("json_schema_extra", {}) or {}
    json_schema_extra["plot"] = {"label": label, "x": x}

    return Field(
        default=default,
        description=description,
        json_schema_extra=json_schema_extra,
        **kwargs,
    )


class Model(BaseModel, extra="forbid", arbitrary_types_allowed=True):

    @classmethod
    def get_xpath(cls, ypath: str, yfield: FieldInfo = None) -> str:
        if yfield is None:
            yfield = cls._resolve_field_path(ypath)

        plot = yfield.json_schema_extra.get("plot", {})
        xpath = plot.get("x", "")
        if "." in ypath:
            parent = ypath.rsplit(".", 1)[0]
            xpath = f"{parent}.{xpath}"
        return xpath

    @classmethod
    def get_xy_labels(
        cls, ypath: str, kweight: Optional[int] = None
    ) -> Tuple[str, str]:
        params = (
            {"kweight": "n", "kweightp1": "(n+1)"}
            if kweight is None
            else {"kweight": kweight, "kweightp1": kweight + 1}
        )

        yfield = cls._resolve_field_path(ypath)
        plot = yfield.json_schema_extra.get("plot", {})
        ylabel = plot.get("label", "").format(**params)

        xpath = cls.get_xpath(ypath, yfield)
        xfield = cls._resolve_field_path(xpath)
        plot = xfield.json_schema_extra.get("plot", {})
        xlabel = plot.get("label", "").format(**params)

        return xlabel, ylabel

    def get_value(self, path: str) -> Any:
        parts = path.split(".")
        value = self
        for part in parts:
            value = getattr(value, part)
        return value

    @classmethod
    def _resolve_field_path(cls, path: str) -> FieldInfo:
        """
        Resolve a dotted field path like 'ft.intensity' or 'chi'
        and return the corresponding FieldInfo.
        """
        parts = path.split(".")
        current_model: type[Model] = cls

        for i, part in enumerate(parts):
            if part not in current_model.model_fields:
                raise KeyError(
                    f"Field '{part}' not found on {current_model.__name__} "
                    f"(while resolving '{path}')"
                )

            field_info = current_model.model_fields[part]

            # If this is the last part, return the field
            if i == len(parts) - 1:
                return field_info

            # Otherwise, descend into the annotation
            annotation = field_info.annotation
            origin = get_origin(annotation)

            next_model = None

            # Handle Optional[...] / Union[...]
            if origin is not None:
                for arg in get_args(annotation):
                    if isinstance(arg, type) and issubclass(arg, Model):
                        next_model = arg
                        break
            elif isinstance(annotation, type) and issubclass(annotation, Model):
                next_model = annotation

            if next_model is None:
                raise KeyError(
                    f"Field '{part}' on {current_model.__name__} "
                    f"is not a nested Model (while resolving '{path}')"
                )

            current_model = next_model

        raise KeyError(f"Invalid field path '{path}'")


class FT(Model):
    radius: Optional[numpy.ndarray] = SpectrumField(
        label="Radius (Å)",
        description="Radial distance R",
    )

    intensity: Optional[numpy.ndarray] = SpectrumField(
        label="|FT(R)| (Å^-{kweightp1})",
        x="radius",
        description="Magnitude of Fourier-transformed EXAFS signal",
    )

    real: Optional[numpy.ndarray] = SpectrumField(
        label="Re[FT(R)] (Å^-{kweightp1})",
        x="radius",
        description="Real part of the Fourier transform",
    )

    imaginary: Optional[numpy.ndarray] = SpectrumField(
        label="Im[FT(R)] (Å^-{kweightp1})",
        x="radius",
        description="Imaginary part of the Fourier transform",
    )

    phase: Optional[numpy.ndarray] = SpectrumField(
        description="Phase of the Fourier-transformed signal",
    )

    window_weight: Optional[numpy.ndarray] = SpectrumField(
        description="Windowing function applied in k-space",
    )


class LarchResults(Model):
    bkg: Optional[numpy.ndarray] = SpectrumField(
        label="Background μ(E)",
        x="energy",
        description="Background function estimated by Larch autobk",
    )

    xftf_k_weight: Optional[float] = SpectrumField(
        description="k-weight applied during Larch xftf",
    )

    xftf_k_min: Optional[float] = SpectrumField(
        description="Minimum k used for Larch Fourier transform",
    )

    xftf_k_max: Optional[float] = SpectrumField(
        description="Maximum k used for Larch Fourier transform",
    )


class PymcaResults(Model):
    PostEdgeK: Optional[numpy.ndarray] = SpectrumField(
        label="Wavenumber (Å^-1)",
        description="Photoelectron wavenumber in the post-edge region",
    )

    PostEdgeB: Optional[numpy.ndarray] = SpectrumField(
        label="Post-edge background",
        x="PostEdgeK",
        description="Post-edge background signal",
    )

    EXAFSNormalized: Optional[numpy.ndarray] = SpectrumField(
        label="χ(k)",
        x="PostEdgeK",
        description="Normalized EXAFS signal",
    )

    KMin: Optional[float] = SpectrumField(
        description="Minimum k value selected for EXAFS processing",
    )

    KMax: Optional[float] = SpectrumField(
        description="Maximum k value selected for EXAFS processing",
    )

    KWeight: Optional[float] = SpectrumField(
        description="k-weight exponent applied to EXAFS signal",
    )

    KnotsX: Optional[numpy.ndarray] = SpectrumField(
        label="Knots X",
        description="X-coordinates of spline knots",
    )

    KnotsY: Optional[numpy.ndarray] = SpectrumField(
        label="Knots Y",
        x="KnotsX",
        description="Y-coordinates of spline knots",
    )


class Spectrum(Model):
    energy: Optional[numpy.ndarray] = SpectrumField(
        label="Energy (eV)",
        description="Energy array",
    )

    mu: Optional[numpy.ndarray] = SpectrumField(
        label="μ (a.u)",
        x="energy",
        description="Absorption coefficient μ(E)",
    )

    x: Optional[int] = SpectrumField(
        description="X index in a spectral map",
    )

    y: Optional[int] = SpectrumField(
        description="Y index in a spectral map",
    )

    k: Optional[numpy.ndarray] = SpectrumField(
        label="Wavenumber (Å^-1)",
        description="Photoelectron wavenumber",
    )

    chi: Optional[numpy.ndarray] = SpectrumField(
        label="χ (a.u)",
        x="k",
        description="EXAFS signal χ(k)",
    )

    chi_weighted_k: Optional[numpy.ndarray] = SpectrumField(
        label="k^{kweight} χ (Å^-{kweight})",
        x="k",
        description="k-weighted EXAFS signal",
    )

    normalized_mu: Optional[numpy.ndarray] = SpectrumField(
        label="Norm(μ) (a.u)",
        x="energy",
        description="Normalized absorption spectrum",
    )

    flatten_mu: Optional[numpy.ndarray] = SpectrumField(
        label="Flat(μ) (a.u)",
        x="energy",
        description="Flattened absorption spectrum",
    )

    normalized_energy: Optional[numpy.ndarray] = SpectrumField(
        label="Normalized energy",
        description="Energy normalized relative to edge position",
    )

    pre_edge: Optional[numpy.ndarray] = SpectrumField(
        description="Pre-edge fitted background",
    )

    post_edge: Optional[numpy.ndarray] = SpectrumField(
        description="Post-edge fitted background",
    )

    edge_step: Optional[float] = SpectrumField(
        description="Absorption edge step",
    )

    e0: Optional[float] = SpectrumField(
        description="Edge energy E0 (eV)",
    )

    noise_savgol: Optional[numpy.ndarray] = SpectrumField(
        label="Noise(μ) (a.u)",
        x="energy",
        description="Noise estimated using Savitzky-Golay filtering",
    )

    raw_noise_savgol: Optional[numpy.ndarray] = SpectrumField(
        description="Raw noise from Savitzky-Golay filtering",
    )

    norm_noise_savgol: Optional[numpy.ndarray] = SpectrumField(
        description="Normalized noise from Savitzky-Golay filtering",
    )

    noise_e_min: Optional[float] = SpectrumField(
        description="Lower energy bound used for noise estimation (eV)",
    )

    noise_e_max: Optional[float] = SpectrumField(
        description="Upper energy bound used for noise estimation (eV)",
    )

    ft: FT = Field(
        default_factory=FT,
        description="Fourier transform results",
    )

    pymca_dict: PymcaResults = Field(
        default_factory=PymcaResults,
        description="Results from PyMca EXAFS processing",
    )

    larch_dict: LarchResults = Field(
        default_factory=LarchResults,
        description="Results from Larch EXAFS processing",
    )
