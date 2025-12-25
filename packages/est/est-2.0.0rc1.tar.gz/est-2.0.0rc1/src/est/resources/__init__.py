import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from typing import Optional

if sys.version_info < (3, 9):
    import importlib_resources
else:
    import importlib.resources as importlib_resources

from .generate import save_3d_exafs


@contextmanager
def resource_path(*args) -> Generator[Path, None, None]:
    """The resource is specified relative to the package "est.resources".

    .. code-block:: python

        with resource_path("icons", "est.png") a path:
            ...
    """
    source = importlib_resources.files(__name__).joinpath(*args)
    with importlib_resources.as_file(source) as path:
        yield path


@contextmanager
def tutorial_workflow(*args) -> Generator[Path, None, None]:
    """The resource is specified relative to the package "orangecontrib.est.tutorial".

    .. code-block:: python

        with tutorial_workflow("example_bm23.ows") a path:
            ...
    """
    import orangecontrib.est.tutorials

    source = importlib_resources.files(orangecontrib.est.tutorials.__name__).joinpath(
        *args
    )
    with importlib_resources.as_file(source) as path:
        yield path


def generate_resource(
    *args,
    cache: bool = True,
    overwrite: bool = False,
    output_directory: Optional[str] = None,
    word="EXAMPLE",
) -> Path:
    """Generate the derived resource from project `resource` when it does not
    exist or when `overwrite=True`. The directory in which the resource is
    located in either

    * the directory specified by argument `output_directory`
    * the user's cache directory (`cache=True`, this is the default)
    * a temporary directory (`cache=False`)
    """
    with resource_path(*args) as infile:
        assert infile.parent.name == "exafs"
        outname = infile.stem + ".h5"
        if output_directory:
            outdir = Path(output_directory)
        elif cache:
            outdir = get_user_resource_dir()
        else:
            outdir = Path(tempfile.gettempdir())
        outfile = outdir / outname
        if not outfile.exists() or overwrite:
            save_3d_exafs(infile, outfile, word=word)
        return outfile


def get_user_resource_dir() -> Path:
    path = get_user_cache_dir() / "resources"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_user_cache_dir() -> Path:
    home = Path().home()
    if sys.platform == "darwin":
        path = home / "Library" / "Caches"
    elif sys.platform == "win32":
        path = home / "AppData" / "Local"
        path = os.getenv("APPDATA", path)
    elif os.name == "posix":
        path = home / ".cache"
        path = os.getenv("XDG_CACHE_HOME", path)
    else:
        path = home / ".cache"

    if sys.platform == "win32":
        # On Windows cache and data dir are the same.
        # Microsoft suggest using a Cache subdirectory
        return path / "est" / "Cache"
    else:
        return path / "est"
