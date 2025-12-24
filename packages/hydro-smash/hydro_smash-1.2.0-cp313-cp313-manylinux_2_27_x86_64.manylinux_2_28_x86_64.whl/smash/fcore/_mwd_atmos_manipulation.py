"""
(MW) Module Wrapped and Differentiated.

Subroutine
----------

- get_atmos_data_timestep
- set_atmos_data_timestep
- get_ac_atmos_data_timestep
- set_ac_atmos_data_timestep

Module mwd_atmos_manipulation
Defined at ../smash/fcore/routine/mwd_atmos_manipulation.f90 lines 10-115
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

def get_atmos_data_time_step(self, mesh, input_data, time_step, key, vle, \
    interface_call=False):
    """
    assert(setup%snow_module_present)
    assert(setup%snow_module_present)
    only: sp
    only: SetupDT
    only: MeshDT
    only: Input_DataDT
    only: sparse_matrix_to_matrix, matrix_to_sparse_matrix, &
    ac_vector_to_matrix, matrix_to_ac_vector
    
    get_atmos_data_time_step(self, mesh, input_data, time_step, key, vle)
    Defined at ../smash/fcore/routine/mwd_atmos_manipulation.f90 lines 19-54
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    time_step : int32
    key : str
    vle : float array
    """
    _libfcore.f90wrap_mwd_atmos_manipulation__get_atmos_data_time_step(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, time_step=time_step, \
        key=key, vle=vle)

def set_atmos_data_time_step(self, mesh, input_data, time_step, key, vle, \
    interface_call=False):
    """
    assert(setup%snow_module_present)
    assert(setup%snow_module_present)
    
    set_atmos_data_time_step(self, mesh, input_data, time_step, key, vle)
    Defined at ../smash/fcore/routine/mwd_atmos_manipulation.f90 lines 56-91
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    time_step : int32
    key : str
    vle : float array
    """
    _libfcore.f90wrap_mwd_atmos_manipulation__set_atmos_data_time_step(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, time_step=time_step, \
        key=key, vle=vle)

def get_ac_atmos_data_time_step(self, mesh, input_data, time_step, key, \
    ac_vector, interface_call=False):
    """
    get_ac_atmos_data_time_step(self, mesh, input_data, time_step, key, ac_vector)
    Defined at ../smash/fcore/routine/mwd_atmos_manipulation.f90 lines 93-103
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    time_step : int32
    key : str
    ac_vector : float array
    """
    _libfcore.f90wrap_mwd_atmos_manipulation__get_ac_atmos_data_time_step(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, time_step=time_step, \
        key=key, ac_vector=ac_vector)

def set_ac_atmos_data_time_step(self, mesh, input_data, time_step, key, \
    ac_vector, interface_call=False):
    """
    set_ac_atmos_data_time_step(self, mesh, input_data, time_step, key, ac_vector)
    Defined at ../smash/fcore/routine/mwd_atmos_manipulation.f90 lines 105-115
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    time_step : int32
    key : str
    ac_vector : float array
    """
    _libfcore.f90wrap_mwd_atmos_manipulation__set_ac_atmos_data_time_step(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, time_step=time_step, \
        key=key, ac_vector=ac_vector)


_array_initialisers = []
_dt_array_initialisers = []

try:
    for func in _array_initialisers:
        func()
except ValueError:
    logger.debug('unallocated array(s) detected on import of module \
        "mwd_atmos_manipulation".')

for func in _dt_array_initialisers:
    func()
