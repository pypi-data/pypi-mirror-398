import logging
import os
from glob import glob
from pathlib import Path
from typing import Dict
from typing import List
from typing import Tuple

import h5py
import numpy
from numpy.typing import ArrayLike

try:
    import PIL.Image
    import PIL.ImageDraw
    import PIL.ImageFont

    has_PIL = True
except ImportError:
    has_PIL = False

logger = logging.getLogger(__name__)

DataDict = Dict[str, ArrayLike]


def save_3d_exafs(infile: Path, outfile: Path, word="EXAMPLE") -> None:
    """Save a 1D EXAFS spectrum as 3D scan data (fullfield or fluoxas)

    :param Path infile: ASCII file containing EXAFS spectrum
    :param Path outfile: output hdf5 file
    """
    lst = numpy.loadtxt(infile).T
    if len(lst) == 3:
        energy, mu, i0 = lst
    else:
        energy, mu = lst
        i0 = numpy.ones_like(mu)
    it = i0 * numpy.exp(-mu)
    data = {"mu": mu, "i0": i0, "it": it}
    generate_3d_exafs(str(infile), energy, data, outfile, word=word)
    return outfile


def generate_3d_exafs(
    filename: str, energy: ArrayLike, data: DataDict, outfile: Path, word="EXAMPLE"
) -> None:
    scannr = 0
    info = {"source": filename}
    positioners = {"energy": energy}
    signals = list(data)
    axes = ["energy"]
    if outfile.exists():
        outfile.unlink()

    info["comment"] = "Bliss energy scan with a 1D detector"
    scannr += 1
    _save_scan(
        outfile,
        f"{scannr}.1",
        "exafs",
        positioners,
        data,
        signals,
        axes,
        "spectrum",
        info,
    )

    im = _generate_test_image(word)
    data = {
        k: numpy.multiply.outer(v, im) for k, v in data.items()
    }  # Axes: energy, y, x
    nenergy = len(energy)

    ny, nx = im.shape

    step_size = 1
    xstart = -nx / 3
    xstop = xstart + step_size * (nx - 1)
    x = numpy.linspace(xstart, xstop, nx)

    ystop = 10
    ystart = ystop + step_size * (ny - 1)
    y = numpy.linspace(ystart, ystop, ny)

    positioners["x"] = x
    positioners["y"] = y
    for name, values in positioners.items():
        info[f"n{name}"] = len(values)

    axes = ["energy", "y", "x"]
    dimensions = (axes.index("x"), axes.index("y"), axes.index("energy"))
    info["dimensions"] = dimensions
    info["comment"] = "Bliss energy scan with a 2D detector"
    tmp = next(iter(data.values()))
    assert tmp.shape[dimensions[0]] == nx
    assert tmp.shape[dimensions[1]] == ny
    assert tmp.shape[dimensions[2]] == nenergy
    scannr += 1
    _save_scan(
        outfile,
        f"{scannr}.1",
        "fullfield exafs",
        positioners,
        data,
        signals,
        axes,
        None,
        info,
    )

    axes = ["y", "x", "energy"]
    dimensions = (axes.index("x"), axes.index("y"), axes.index("energy"))
    prev_dimensions = info["dimensions"]
    info["dimensions"] = dimensions
    info["comment"] = (
        "Bliss mesh scan (Y is the fast axis) at multiple energies with a 1D detector"
    )
    data = {k: numpy.moveaxis(v, prev_dimensions, dimensions) for k, v in data.items()}
    tmp = next(iter(data.values()))
    assert tmp.shape[dimensions[0]] == nx
    assert tmp.shape[dimensions[1]] == ny
    assert tmp.shape[dimensions[2]] == nenergy
    scannr += 1
    fpositioners, fdata = _flatten_mesh_scan(axes, positioners, data)
    title = f"fluoxas y {ystart} {ystop} {nx-1} x {xstart} {xstop} {nx-1}"
    _save_scan(
        outfile,
        f"{scannr}.1",
        title,
        fpositioners,
        fdata,
        list(),
        list(),
        None,
        info,
    )

    axes = ["x", "y", "energy"]
    dimensions = (axes.index("x"), axes.index("y"), axes.index("energy"))
    prev_dimensions = info["dimensions"]
    info["dimensions"] = dimensions
    info["comment"] = (
        "Bliss mesh scan (X is the fast axis) at multiple energies with a 1D detector"
    )
    data = {k: numpy.moveaxis(v, prev_dimensions, dimensions) for k, v in data.items()}
    tmp = next(iter(data.values()))
    assert tmp.shape[dimensions[0]] == nx
    assert tmp.shape[dimensions[1]] == ny
    assert tmp.shape[dimensions[2]] == nenergy
    scannr += 1
    fpositioners, fdata = _flatten_mesh_scan(axes, positioners, data)
    title = f"fluoxas x {xstart} {xstop} {nx-1} y {ystart} {ystop} {nx-1}"
    _save_scan(
        outfile,
        f"{scannr}.1",
        title,
        fpositioners,
        fdata,
        list(),
        list(),
        None,
        info,
    )

    axes = ["energy", "x", "y"]
    dimensions = (axes.index("x"), axes.index("y"), axes.index("energy"))
    prev_dimensions = info["dimensions"]
    info["dimensions"] = dimensions
    info["comment"] = (
        "Bliss energy scan at grid positions (X is the fast axis)with a 1D detector"
    )
    data = {k: numpy.moveaxis(v, prev_dimensions, dimensions) for k, v in data.items()}
    tmp = next(iter(data.values()))
    assert tmp.shape[dimensions[0]] == nx
    assert tmp.shape[dimensions[1]] == ny
    assert tmp.shape[dimensions[2]] == nenergy
    scannr += 1
    fpositioners, fdata = _flatten_mesh_scan(axes, positioners, data)
    title = f"exafsgrid x {xstart} {xstop} {nx-1} y {ystart} {ystop} {nx-1}"
    _save_scan(
        outfile,
        f"{scannr}.1",
        title,
        fpositioners,
        fdata,
        list(),
        list(),
        None,
        info,
    )

    axes = ["energy", "y", "x"]
    dimensions = (axes.index("x"), axes.index("y"), axes.index("energy"))
    prev_dimensions = info["dimensions"]
    info["dimensions"] = dimensions
    info["comment"] = (
        "Bliss energy scan at grid positions (Y is the fast axis) with a 1D detector"
    )
    data = {k: numpy.moveaxis(v, prev_dimensions, dimensions) for k, v in data.items()}
    tmp = next(iter(data.values()))
    assert tmp.shape[dimensions[0]] == nx
    assert tmp.shape[dimensions[1]] == ny
    assert tmp.shape[dimensions[2]] == nenergy
    scannr += 1
    fpositioners, fdata = _flatten_mesh_scan(axes, positioners, data)
    title = f"exafsgrid y {ystart} {ystop} {nx-1} x {xstart} {xstop} {nx-1}"
    _save_scan(
        outfile,
        f"{scannr}.1",
        title,
        fpositioners,
        fdata,
        list(),
        list(),
        None,
        info,
    )

    with h5py.File(outfile, "a") as h5f:
        h5f.attrs["default"] = "1.1"


def _save_scan(
    filename: str,
    scan: str,
    title: str,
    positioners: DataDict,
    data: DataDict,
    plot_signals: List[str],
    plot_axes: List[str],
    interpretation: str,
    info: dict,
) -> None:
    with h5py.File(filename, "a") as h5f:
        h5f.attrs["NX_class"] = "NXroot"

        entry = h5f.create_group(scan)
        url = f"{filename}::{entry.name}"
        entry.attrs["NX_class"] = "NXentry"
        entry["title"] = title

        dinfo = entry.create_group("info")
        dinfo.attrs["NX_class"] = "NXnote"
        if info is not None:
            for k, v in info.items():
                dinfo[k] = v

        if plot_signals:
            plotselect = entry.create_group("plotselect")
            plotselect.attrs["NX_class"] = "NXdata"

        instrument = entry.create_group("instrument")
        instrument.attrs["NX_class"] = "NXinstrument"

        measurement = entry.create_group("measurement")
        measurement.attrs["NX_class"] = "NXconnection"

        for name, values in positioners.items():
            grp = instrument.create_group(name)
            grp.attrs["NX_class"] = "NXpositioner"
            grp["value"] = values
            if name == "energy":
                grp["value"].attrs["units"] = "eV"
            dest = grp["value"].name
            measurement[name] = h5py.SoftLink(dest)
            if name in plot_axes:
                plotselect[name] = h5py.SoftLink(dest)

        for name, values in data.items():
            grp = instrument.create_group(name)
            grp.attrs["NX_class"] = "NXdetector"
            grp["data"] = values
            dest = grp["data"].name
            measurement[name] = h5py.SoftLink(dest)
            if name in plot_signals:
                plotselect[name] = h5py.SoftLink(dest)

        if plot_signals:
            h5f.attrs["default"] = scan
            entry.attrs["default"] = "plotselect"
            plotselect.attrs["signal"] = plot_signals[0]
            if len(plot_signals) > 1:
                plotselect.attrs["auxiliary_signals"] = plot_signals[1:]
            if plot_axes:
                plotselect.attrs["axes"] = plot_axes
            if interpretation:
                plotselect.attrs["interpretation"] = interpretation
    logger.info("SAVED %s (%s)", url, info["comment"])


def _generate_test_image(text: str) -> numpy.ndarray:
    if not has_PIL:
        return numpy.ones((15, 23))
    fontsize = 28
    if os.name == "nt":
        font = PIL.ImageFont.truetype("Arial.ttf", fontsize)
    else:
        files = glob("/usr/share/fonts/truetype/*/*.ttf")
        for filename in files:
            if "arial" in filename.lower():
                break
        font = PIL.ImageFont.truetype(filename, fontsize)

    left, top, right, bottom = font.getbbox(text)
    width, height = right, bottom

    off = 10
    canvas = PIL.Image.new("RGB", (width + off, height + off), "black")
    draw = PIL.ImageDraw.Draw(canvas)
    draw.text((off / 2, off / 2), text, fill="red", font=font)

    img = numpy.asarray(canvas, dtype=bool)[..., 0]
    return img


def _flatten_mesh_scan(
    axes: List[str], positioners: DataDict, data: DataDict
) -> Tuple[DataDict, DataDict]:
    # Axes: fast axis, slow axis, energy axis
    # Data shape: fast axis, slow axis, energy axis
    fast = positioners[axes[0]]
    slow = positioners[axes[1]]
    energy = positioners[axes[2]]
    shape = (fast.size, slow.size, energy.size)

    fast = fast[:, None, None]
    slow = slow[None, :, None]
    energy = energy[None, None, :]
    fast = numpy.tile(fast, (1, shape[1], shape[2]))
    slow = numpy.tile(slow, (shape[0], 1, shape[2]))
    energy = numpy.tile(energy, (shape[0], shape[1], 1))

    positioners = {
        axes[0]: fast.flatten(),
        axes[1]: slow.flatten(),
        axes[2]: energy.flatten(),
    }
    data = {k: v.flatten() for k, v in data.items()}
    return positioners, data
