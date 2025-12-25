import argparse
import signal
import sys

from silx.gui import qt

from ..core.units import as_energy_unit
from ..gui.xas_object_definition.window import XASObjectWindow
from .utils.url import get_url


def _plot(
    spec_input,
    input_spectra_url,
    input_spectra_dims,
    input_channel_url,
    input_energy_unit,
):
    has_url_information = input_spectra_url or input_channel_url
    (
        input_ascii_file,
        input_energy_col_name,
        input_abs_col_name,
        input_monitor_col_name,
        scan_title,
    ) = spec_input
    if input_ascii_file is not None and has_url_information:
        raise ValueError("You cannot provide an input file and input urls")

    app = qt.QApplication([])
    widget = XASObjectWindow(parent=None)
    if input_ascii_file is not None:
        # warning: the file should set prior to col names... because
        # they need to be defined
        widget.setAsciiFile(input_ascii_file)
        widget.setCurrentType("ascii")

        if input_energy_col_name is not None:
            widget.setEnergyColName(input_energy_col_name)
        if input_abs_col_name is not None:
            widget.setAbsColName(input_abs_col_name)
        if scan_title is not None:
            widget.setScanTitle(scan_title)
        if input_monitor_col_name is not None:
            widget.setMonitorColName(input_monitor_col_name)
    else:
        widget.setSpectraUrl(input_spectra_url)
        widget.setEnergyUrl(input_channel_url)
        widget.setCurrentType("hdf5")
    widget.setEnergyUnit(input_energy_unit)
    widget.setDimensions(input_spectra_dims)
    widget.loadXasObject()
    widget.show()

    qt.QLocale.setDefault(qt.QLocale(qt.QLocale.English))
    qt.QLocale.setDefault(qt.QLocale.c())
    signal.signal(signal.SIGINT, sigintHandler)
    sys.excepthook = qt.exceptionHandler
    timer = qt.QTimer()
    timer.start(500)
    # Application have to wake up Python interpreter, else SIGINT is not
    # catch
    timer.timeout.connect(lambda: None)

    app.exec_()


def sigintHandler(*args):
    """Handler for the SIGINT signal."""
    qt.QApplication.quit()


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    # single file input option
    parser.add_argument(
        "-i",
        "--input",
        dest="input_",
        default=None,
        help="Input of the workflow. Should be a path to a file",
    )
    # input url option
    parser.add_argument(
        "--input-spectra",
        "--spectra",
        dest="input_spectra",
        default=None,
        help="Input spectra url",
    )
    parser.add_argument(
        "--input-spectra-dims",
        "--spectra-dims",
        dest="input_spectra_dims",
        nargs=3,
        type=int,
        default=None,
        help="spectra dimension. Should be a tuple of three values like: (Z,Y,X)",
    )
    parser.add_argument(
        "--input-channel",
        "--channel",
        dest="input_channel",
        default=None,
        help="Input channel url (usually energy)",
    )
    parser.add_argument(
        "--input-energy-unit",
        "--energy-unit",
        dest="input_energy_unit",
        default="eV",
        help="energy unit",
    )
    parser.add_argument(
        "--input-energy-col-name",
        "--energy-col-name",
        dest="input_energy_col_name",
        default=None,
        help="Provide name of the energy column for spec file",
    )
    parser.add_argument(
        "--input-abs-col-name",
        "--abs-col-name",
        dest="input_abs_col_name",
        default=None,
        help="Provide name of the absorption column for spec file",
    )
    parser.add_argument(
        "--input-monitor-col-name",
        "--monitor-col-name",
        dest="input_monitor_col_name",
        default=None,
        help="Provide name of the monitor column for spec file",
    )
    parser.add_argument(
        "--input-scan-title",
        "--scan-title",
        dest="input_scan_title_name",
        default=None,
        help="Provide scan title name to consider",
    )
    options = parser.parse_args(argv[1:])

    _plot(
        spec_input=(
            options.input_,
            options.input_energy_col_name,
            options.input_abs_col_name,
            options.input_monitor_col_name,
            options.input_scan_title_name,
        ),
        input_spectra_url=get_url(options.input_spectra),
        input_spectra_dims=options.input_spectra_dims,
        input_channel_url=get_url(options.input_channel),
        input_energy_unit=as_energy_unit(options.input_energy_unit),
    )


if __name__ == "__main__":
    main(sys.argv)
