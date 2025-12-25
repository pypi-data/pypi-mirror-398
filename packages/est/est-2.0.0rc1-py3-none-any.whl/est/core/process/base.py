"""module for process base class"""

from importlib.metadata import version as get_version
from typing import Callable
from typing import List
from typing import Union

from ewokscore.taskwithprogress import TaskWithProgress as Task

from ..types.xasobject import XASObject
from ..utils import extract_properties_from_dict
from .progress import Progress

est_version = get_version("est")


class Process(Task, register=False):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._advancement = Progress(name=self.name)
        self.__stop = False
        """flag to notice when a end of process is required"""
        self._settings = {}
        # configuration
        self._callbacks = []

    def __init_subclass__(subclass, name="", **kwargs):
        super().__init_subclass__(**kwargs)
        subclass._NAME = name

    @property
    def name(self) -> str:
        return self._NAME

    def stop(self):
        self.__stop = True

    @property
    def advancement(self):
        return self._advancement

    @advancement.setter
    def advancement(self, advancement):
        assert isinstance(advancement, Progress)
        self._advancement = advancement

    @property
    def callbacks(self) -> List[Callable[[], None]]:
        return self._callbacks

    @staticmethod
    def getXasObject(xas_obj: Union[XASObject, dict]) -> XASObject:
        if isinstance(xas_obj, dict):
            xas_obj = XASObject.from_dict(xas_obj)
        if not isinstance(xas_obj, XASObject):
            raise TypeError("xas_obj must be provided")
        if xas_obj.n_spectrum > 0:
            xas_obj.spectra.check_validity()
        return xas_obj

    def program_name(self) -> str:
        """
        Name of the process to be saved in HDF5.
        """
        return self.class_registry_name().split(".")[-1]

    @staticmethod
    def program_version() -> str:
        """
        Version of the process to be saved in HDF5.
        """
        return est_version

    @staticmethod
    def definition(self) -> str:
        """
        Definition of the process to be saved in HDF5.
        """
        raise NotImplementedError("Base class")

    def getConfiguration(self) -> dict:
        """
        :Parameters of the process to be saved in HDF5.
        """
        return self._settings

    def setConfiguration(self, configuration: dict):
        # filter configuration from orange widgets
        if "__version__" in configuration:
            del configuration["__version__"]
        if "savedWidgetGeometry" in configuration:
            del configuration["savedWidgetGeometry"]
        if "savedWidgetGeometry" in configuration:
            del configuration["savedWidgetGeometry"]
        if "controlAreaVisible" in configuration:
            del configuration["controlAreaVisible"]

        self._settings = configuration

    def addCallback(self, callback):
        self._callbacks.append(callback)

    def update_properties(self, properties):
        if properties is None:
            return
        if isinstance(properties, str):
            properties = extract_properties_from_dict(properties)
        self._settings.update(properties)
