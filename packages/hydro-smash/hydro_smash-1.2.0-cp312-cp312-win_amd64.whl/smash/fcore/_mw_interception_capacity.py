"""
(MW) Module Wrapped.

Subroutine
----------

- adjust_interception_capacity

Module mw_interception_capacity
Defined at ../smash/fcore/routine/mw_interception_capacity.f90 lines 7-90
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

def adjust_interception_capacity(self, mesh, input_data, day_index, nday, ci, \
    interface_call=False):
    """
    =========================================================================================================== \
        %
    Calculate interception storage
    =========================================================================================================== \
        %
    
    adjust_interception_capacity(self, mesh, input_data, day_index, nday, ci)
    Defined at ../smash/fcore/routine/mw_interception_capacity.f90 lines 18-90
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    day_index : int array
    nday : int32
    ci : float array
    """
    _libfcore.f90wrap_mw_interception_capacity__adjust_interception_capacity(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, day_index=day_index, \
        nday=nday, ci=ci)


_array_initialisers = []
_dt_array_initialisers = []

try:
    for func in _array_initialisers:
        func()
except ValueError:
    logger.debug('unallocated array(s) detected on import of module \
        "mw_interception_capacity".')

for func in _dt_array_initialisers:
    func()
