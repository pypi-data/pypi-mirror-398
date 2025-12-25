import numpy
import pytest

try:
    import larch
except ImportError:
    larch = None

from ..core.io.read_xas import read_from_ascii


@pytest.mark.parametrize("extension", ["csv", "xmu", "spec", "dat"])
@pytest.mark.parametrize("nchannels", [0, 10], ids=["nodata", "data"])
@pytest.mark.parametrize("with_monitor", [True, False], ids=["monitor", "nomonitor"])
def test_ascii_reader(tmp_path, extension, nchannels, with_monitor):
    if extension == "xmu" and larch is None:
        pytest.skip("xraylarch not installed")

    filename = str(tmp_path / f"data.{extension}")

    if extension == "csv":
        delimiter = ","
    else:
        delimiter = " "

    if extension == "csv":
        comments = ""
    else:
        comments = "#"

    scan_title = "loopscan"
    energy_col_name = "energy"
    absorption_col_name = "mu"
    monitor_col_name = "monitor"

    if extension == "spec":
        if with_monitor:
            header = [
                f"F {str(filename)}",
                "D Mon Jun 04 14:15:57 2012",
                "",
                f"S 1 {scan_title}",
                "D Mon Jun 04 14:15:57 2012",
                "N 3",
                f"L {energy_col_name}  {absorption_col_name}  {monitor_col_name}",
            ]
        else:
            header = [
                f"F {str(filename)}",
                "D Mon Jun 04 14:15:57 2012",
                "",
                f"S 1 {scan_title}",
                "D Mon Jun 04 14:15:57 2012",
                "N 2",
                f"L {energy_col_name}  {absorption_col_name}",
            ]

        header = "\n".join(header)
        scan_title = f"1 {scan_title}"
    elif extension == "dat":
        header = ""
        energy_col_name = "Column 1"
        absorption_col_name = "Column 2"
        monitor_col_name = "Column 3"
    else:
        if with_monitor:
            header = delimiter.join(["energy", "mu", "monitor"])
        else:
            header = delimiter.join(["energy", "mu"])

    energy = numpy.arange(1, 1 + nchannels)
    mu = numpy.random.randint(low=1, high=100, size=nchannels)
    if with_monitor:
        monitor = numpy.random.randint(low=1, high=100, size=nchannels)
        data = numpy.array([energy, mu, monitor]).T
    else:
        data = numpy.array([energy, mu]).T

    numpy.savetxt(
        filename,
        data,
        delimiter=delimiter,
        comments=comments,
        header=header,
    )

    columns_names = {
        "energy": energy_col_name,
        "mu": absorption_col_name,
        "monitor": monitor_col_name,
    }
    xasobject = read_from_ascii(
        filename, columns_names=columns_names, scan_title=scan_title
    )
    numpy.testing.assert_array_equal(energy, xasobject.energy)
    if with_monitor:
        numpy.testing.assert_array_equal(mu / monitor, xasobject.spectra[0, 0].mu)
    else:
        numpy.testing.assert_array_equal(mu, xasobject.spectra[0, 0].mu)


@pytest.mark.parametrize("extension", ["csv", "xmu", "spec", "dat"])
def test_empty_ascii_file(tmp_path, extension):
    if extension == "xmu" and larch is None:
        pytest.skip("xraylarch not installed")

    filename = str(tmp_path / f"data.{extension}")
    with open(filename, "w"):
        pass

    columns_names = {"energy": "energy", "mu": "mu", "monitor": "monitor"}

    xasobject = read_from_ascii(
        filename, columns_names=columns_names, scan_title="loopscan"
    )
    assert xasobject.energy.size == 0
    assert xasobject.spectra[0, 0].mu.size == 0
