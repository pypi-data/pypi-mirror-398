"""
(MW) Module Wrapped.

Subroutine
----------

- get_flwdst_cls
- get_width_function_cdf
- get_rainfall_weighted_width_function_cdf
- precipitation_indices_computation

Module mw_prcp_indices
Defined at ../smash/fcore/signal_analysis/mw_prcp_indices.f90 lines 10-133
"""
from __future__ import print_function, absolute_import, division
from smash.fcore import _libfcore
import f90wrap.runtime
import logging
import numpy
import warnings
import weakref

logger = logging.getLogger(__name__)
warnings.filterwarnings("error", category=numpy.exceptions.ComplexWarning)
_arrays = {}
_objs = {}

def get_flwdst_cls(flwdst, flwdst_cls, interface_call=False):
    """
    get_flwdst_cls(flwdst, flwdst_cls)
    Defined at ../smash/fcore/signal_analysis/mw_prcp_indices.f90 lines 20-31
    
    Parameters
    ----------
    flwdst : float array
    flwdst_cls : float array
    """
    _libfcore.f90wrap_mw_prcp_indices__get_flwdst_cls(flwdst=flwdst, \
        flwdst_cls=flwdst_cls)

def get_width_function_cdf(flwdst, flwdst_cls, w_cdf, interface_call=False):
    """
    get_width_function_cdf(flwdst, flwdst_cls, w_cdf)
    Defined at ../smash/fcore/signal_analysis/mw_prcp_indices.f90 lines 33-43
    
    Parameters
    ----------
    flwdst : float array
    flwdst_cls : float array
    w_cdf : float array
    """
    _libfcore.f90wrap_mw_prcp_indices__get_width_function_cdf(flwdst=flwdst, \
        flwdst_cls=flwdst_cls, w_cdf=w_cdf)

def get_rainfall_weighted_width_function_cdf(flwdst, flwdst_cls, prcp_matrix, \
    wp_cdf, interface_call=False):
    """
    get_rainfall_weighted_width_function_cdf(flwdst, flwdst_cls, prcp_matrix, \
        wp_cdf)
    Defined at ../smash/fcore/signal_analysis/mw_prcp_indices.f90 lines 45-58
    
    Parameters
    ----------
    flwdst : float array
    flwdst_cls : float array
    prcp_matrix : float array
    wp_cdf : float array
    """
    _libfcore.f90wrap_mw_prcp_indices__get_rainfall_weighted_width_functi3737(flwdst=flwdst, \
        flwdst_cls=flwdst_cls, prcp_matrix=prcp_matrix, wp_cdf=wp_cdf)

def precipitation_indices_computation(self, mesh, input_data, prcp_indices, \
    interface_call=False):
    """
    precipitation_indices_computation(self, mesh, input_data, prcp_indices)
    Defined at ../smash/fcore/signal_analysis/mw_prcp_indices.f90 lines 61-133
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    prcp_indices : float array
    """
    _libfcore.f90wrap_mw_prcp_indices__precipitation_indices_computation(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, prcp_indices=prcp_indices)


_array_initialisers = []
_dt_array_initialisers = []

try:
    for func in _array_initialisers:
        func()
except ValueError:
    logger.debug('unallocated array(s) detected on import of module \
        "mw_prcp_indices".')

for func in _dt_array_initialisers:
    func()
