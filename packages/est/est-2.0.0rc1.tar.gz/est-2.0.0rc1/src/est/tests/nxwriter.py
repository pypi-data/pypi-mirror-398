import multiprocessing
from contextlib import contextmanager
from time import sleep
from typing import Dict

import h5py
from numpy.typing import ArrayLike


def nxwriter(
    filename,
    scan: str,
    positioners: Dict[str, ArrayLike],
    detectors: Dict[str, ArrayLike],
    blocksize: int,
    period: float,
):
    """Write data in chunks of `blocksize` every `period` seconds"""
    with h5py.File(filename, "a") as h5f:
        h5f.attrs["NX_class"] = "NXroot"

        entry = h5f.create_group(scan)
        entry.attrs["NX_class"] = "NXentry"
        entry["title"] = "test EXAFS scan"

        instrument = entry.create_group("instrument")
        instrument.attrs["NX_class"] = "NXinstrument"

        measurement = entry.create_group("measurement")
        measurement.attrs["NX_class"] = "NXconnection"

        datasets = list()

        for name, values in positioners.items():
            grp = instrument.create_group(name)
            grp.attrs["NX_class"] = "NXpositioner"
            dset = grp.create_dataset(
                "value", shape=(0,), dtype=values.dtype, maxshape=(None,)
            )
            datasets.append((values, dset))
            if name == "energy":
                dset.attrs["units"] = "eV"
            measurement[name] = h5py.SoftLink(dset.name)

        for name, values in detectors.items():
            grp = instrument.create_group(name)
            grp.attrs["NX_class"] = "NXdetector"
            dset = grp.create_dataset(
                "data", shape=(0,), dtype=values.dtype, maxshape=(None,)
            )
            datasets.append((values, dset))
            measurement[name] = h5py.SoftLink(dset.name)

        ndone = 0
        ndatasets = len(datasets)
        while ndone != ndatasets:
            ndone = 0
            for values, dset in datasets:
                istart = dset.size
                istop = istart + blocksize
                data = values[istart:istop]
                if data.size == 0:
                    ndone += 1
                    continue
                istop = istart + data.size
                dset.resize(istop, axis=0)
                dset[istart:istop] = data
            h5f.flush()
            print("NXwriter: flushed and sleep for", period, "sec")
            sleep(period)


@contextmanager
def nxwriter_process(*args, timeout=3, **kw):
    p = multiprocessing.Process(target=nxwriter, args=args, kwargs=kw)
    p.start()
    try:
        yield
    finally:
        p.join(timeout)
        if p.is_alive():
            p.kill()
            p.join()
