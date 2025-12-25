import fabio
import numpy
from silx.io.url import DataUrl


def get_dataset(url: DataUrl) -> numpy.ndarray:
    data_slice = url.data_slice()
    if data_slice is None:
        data_slice = (0,)
    if data_slice is None or len(data_slice) != 1:
        raise ValueError("Fabio slice expect a single frame, but %s found" % data_slice)
    index = data_slice[0]
    if not isinstance(index, int):
        raise ValueError(
            "Fabio slice expect a single integer, but %s found" % data_slice
        )

    try:
        try:
            fabio_file = fabio.open(url.file_path())
        except Exception:
            raise IOError(
                "Error while opening %s with fabio (use debug for more information)"
                % url.path()
            )

        if fabio_file.nframes == 1:
            if index != 0:
                raise ValueError(
                    "Only a single frame available. Slice %s out of range" % index
                )
            return fabio_file.data
        return fabio_file.getframe(index).data
    finally:
        # There is no explicit close
        fabio_file = None
