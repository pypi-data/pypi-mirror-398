import time

import pytest

try:
    import larch
except ImportError:
    larch = None

from ..core.io._utils.load import load_data
from .nxwriter import nxwriter_process
from .test_example_workflows import assert_execution


@pytest.mark.parametrize("period", [0.01, 0.1, 0.5])
def test_get_hdf5_data(period, spectrum_cu_from_larch, tmpdir):
    filename = str(tmpdir / "data.h5")
    scan = "1.1"
    npoints = len(spectrum_cu_from_larch.energy)
    positioners = {"energy": spectrum_cu_from_larch.energy}
    detectors = {"mu": spectrum_cu_from_larch.mu}
    npoints = spectrum_cu_from_larch.energy.size
    blocksize = max(int(npoints / 10), 1)
    est_time = npoints / blocksize * period
    tmax = time.time() + est_time + 5
    print("Estimated scan time", est_time, "s")

    urls = [
        f"silx://{filename}::/{scan}/measurement/energy",
        f"silx://{filename}::/{scan}/measurement/mu",
    ]
    with nxwriter_process(filename, scan, positioners, detectors, blocksize, period):
        nprogress = 0
        while nprogress != npoints:
            data = [load_data(url, retry_timeout=3) for url in urls]
            progress = [len(arr) for arr in data]
            print("Reader point progress", progress)
            nprogress = min(progress)
            if time.time() > tmax:
                raise TimeoutError
            time.sleep(period / 10)


@pytest.mark.skipif(larch is None, reason="larch is not installed")
@pytest.mark.parametrize("period", [0.01, 0.1, 0.5])
def test_live_example_bm23(period, example_bm23, spectrum_cu_from_larch, tmpdir):
    filename = str(tmpdir / "data.h5")
    scan = "1.1"
    npoints = len(spectrum_cu_from_larch.energy)
    positioners = {"energy": spectrum_cu_from_larch.energy}
    detectors = {"mu": spectrum_cu_from_larch.mu}
    npoints = spectrum_cu_from_larch.energy.size
    blocksize = max(int(npoints / 10), 1)
    est_time = npoints / blocksize * period
    tmax = time.time() + est_time + 5
    print("Estimated scan time", est_time, "s")

    input_information = {
        "channel_url": f"silx://{filename}::/{scan}/measurement/energy",
        "spectra_url": f"silx://{filename}::/{scan}/measurement/mu",
        "energy_unit": "electron_volt",
    }

    with nxwriter_process(filename, scan, positioners, detectors, blocksize, period):
        nprogress = 0
        while nprogress != npoints:
            try:
                result = assert_execution(
                    example_bm23, list(), input_information, tmpdir, None
                )
            except RuntimeError:
                pass  # Task error
            else:
                spectrum = next(iter(result["xas_obj"].spectra.data.flat))
                progress = [result["xas_obj"].energy.size, spectrum.mu.size]
                print("Reader point progress", progress)
                nprogress = min(progress)
            if time.time() > tmax:
                break
            time.sleep(period / 10)
