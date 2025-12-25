from ewokscore.task import Task

from ..split import split_bliss_scan


class SplitBlissScan(
    Task,
    input_names=["filename", "scan_number", "monotonic_channel", "out_filename"],
    optional_input_names=[
        "trim_n_points",
        "subscan_size",
        "wait_finished",
        "retry_timeout",
        "retry_period",
        "counter_group",
    ],
    output_names=["out_urls"],
):
    """Split a Bliss scan in subscans as determined by a channel which
    is monotonically increasing or descreasing in each subscan or determined
    by subscan size.

    :param input_names:

    * ``filename``: HDF5 file name containing the Bliss scan.
    * ``scan_number``: The Bliss scan number.
    * ``monotonic_channel``: HDF5 path relative to the scan group.
    * ``out_filename``: HDF5 file name to save subscans as a result of splitting the Bliss scan.

    :param optional_input_names:

    * ``subscan_size``: Fix length subscan size.
    * ``trim_n_points``: Trim N points from the start and end of each subscan.
    * ``wait_finished``: Wait for the Bliss scan to be complete in HDF5.
    * ``retry_timeout``: Timeout of waiting for the Bliss scan to be complete in HDF5.
    * ``retry_period``: Check period of waiting for the Bliss scan to be complete in HDF5.
    * ``counter_group``: Group of counters to check whether a subscan is fully complete.

    :param output_names:

    * ``out_urls``: HDF5 URL's of the subscans as a result of splitting the Bliss scan.
    """

    def run(self):
        self.outputs.out_urls = split_bliss_scan(**self.get_input_values())
