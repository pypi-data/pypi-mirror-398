"""Set of icons for buttons.

Use :func:`getQIcon` to create Qt QIcon from the name identifying an icon.
"""

import logging
import weakref
from contextlib import ExitStack
from contextlib import contextmanager
from typing import Generator
from typing import List

from silx.gui import qt

from .. import resources

_logger = logging.getLogger(__name__)


_cached_icons = None
"""Cache loaded icons in a weak structure"""


def getIconCache():
    """Get access to all cached icons

    :rtype: dict
    """
    global _cached_icons
    if _cached_icons is None:
        _cached_icons = weakref.WeakValueDictionary()
        # Clean up the cache before leaving the application
        # See https://github.com/silx-kit/silx/issues/1771
        qt.QApplication.instance().aboutToQuit.connect(cleanIconCache)
    return _cached_icons


def cleanIconCache():
    """Clean up the icon cache"""
    _cached_icons.clear()


_supported_formats = None
"""Order of file format extension to check"""


def _get_supported_formats() -> List[str]:
    global _supported_formats
    if _supported_formats is None:
        _supported_formats = []
        supported_formats = qt.supportedImageFormats()
        order = ["mng", "gif", "svg", "png", "jpg"]
        for format_ in order:
            if format_ in supported_formats:
                _supported_formats.append(format_)
        if len(_supported_formats) == 0:
            _logger.error("No format supported for icons")
        else:
            _logger.debug("Format %s supported", ", ".join(_supported_formats))
    return _supported_formats


def getQIcon(name: str) -> qt.QIcon:
    """Create a QIcon from its name.

    :param str name: Name of the icon.
    :return: Corresponding QIcon
    :raises: ValueError when name is not known
    """
    cached_icons = getIconCache()
    if name not in cached_icons:
        with _getIconQFile(name) as qfile:
            icon = qt.QIcon(qfile.fileName())
        cached_icons[name] = icon
    else:
        icon = cached_icons[name]
    return icon


@contextmanager
def _getIconQFile(name: str) -> Generator[qt.QFile, None, None]:
    """Create a QFile from an icon name. Filename is found
    according to supported Qt formats.

    :param str name: Name of the icon.
    :return: Corresponding QFile
    :rtype: qt.QFile
    :raises: ValueError when name is not known
    """
    with ExitStack() as stack:
        for format_ in _get_supported_formats():
            ctx = resources.resource_path("icons", f"{name}.{format_}")
            path = stack.enter_context(ctx)
            if not path.exists():
                continue
            yield qt.QFile(str(path))
            return
    raise ValueError("Not an icon name: %s" % name)
