import logging

import numpy
from Orange.data import ContinuousVariable
from Orange.data import Domain
from Orange.data import Table

from ..types.xasobject import XASObject

_logger = logging.getLogger(__name__)


class Converter:
    """This converter ensure a minimal conversion between xas_object and
    Orange.data.Table by only storing energy and absorbed beam (mu)"""

    @staticmethod
    def toXASObject(data_table):
        energy = _retrieve_energy(data_table.domain)
        mu = data_table.X
        mu = numpy.swapaxes(mu, 1, 0)
        print("mu shape is", mu.shape)
        mu = mu.reshape(mu.shape[0], mu.shape[1], -1)
        # note: for now we only consider 2D spectra...
        return XASObject(
            energy=energy, spectra=mu, dim2=mu.shape[-1], dim1=mu.shape[-2]
        )

    @staticmethod
    def toDataTable(xas_object):
        _logger.warning(
            "casting xas_object to Orange.data.Table might bring "
            "lost of some information (process flow, "
            "treatment result...). Only keep energy and absorbed "
            "beam information"
        )
        # TODO: prendre normalized_mu and normalized_energy if exists,
        # otherwise take mu and energy...
        spectra = xas_object.spectra.as_ndarray("mu")
        # invert dimensions and axis to fit spectroscopy add-on
        X = spectra.reshape((spectra.shape[0], -1))
        X = numpy.swapaxes(X, 0, 1)
        domain = Domain(
            attributes=[ContinuousVariable.make("%f" % f) for f in xas_object.energy]
        )
        data = Table.from_numpy(domain=domain, X=X)
        return data


def _retrieve_energy(domain):
    """
    Return x of the data. If all attribute names are numbers,
    return their values. If not, return indices.
    """
    energy = numpy.arange(len(domain.attributes), dtype="f")
    try:
        energy = numpy.array([float(a.name) for a in domain.attributes])
    except Exception:
        _logger.error("fail to retrieve energy from attributes")
    return energy
