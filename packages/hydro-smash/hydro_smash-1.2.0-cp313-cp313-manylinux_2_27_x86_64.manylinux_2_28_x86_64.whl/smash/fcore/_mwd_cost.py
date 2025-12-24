"""
(MWD) Module Wrapped and Differentiated.

Subroutine
----------

- discharge_transformation
- bayesian_compute_cost
- classical_compute_jobs
- classical_compute_cost
- compute_cost

Function
--------

- get_range_event

Module mwd_cost
Defined at ../smash/fcore/cost/mwd_cost.f90 lines 16-403
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

def get_range_event(mask_event, i_event, interface_call=False):
    """
    only: compute_logPost, PriorType
    only: sp, dp
    only: quantile1d_r
    only: nse, nnse, kge, mae, mape, mse, rmse, lgrm
    only: rc, rchf, rclf, rch2r, cfp, ebf, elt, eff
    only: prior_regularization, smoothing_regularization
    only: SetupDT
    only: MeshDT
    only: Input_DataDT
    only: ParametersDT
    only: OutputDT
    only: OptionsDT
    only: ReturnsDT
    
    res = get_range_event(mask_event, i_event)
    Defined at ../smash/fcore/cost/mwd_cost.f90 lines 32-50
    
    Parameters
    ----------
    mask_event : int array
    i_event : int32
    
    Returns
    -------
    res : int array
    """
    res = _libfcore.f90wrap_mwd_cost__get_range_event(mask_event=mask_event, \
        i_event=i_event)
    return res

def discharge_tranformation(tfm, qo, qs, interface_call=False):
    """
    Should be reach by "keep" only. Do nothing
    
    discharge_tranformation(tfm, qo, qs)
    Defined at ../smash/fcore/cost/mwd_cost.f90 lines 52-70
    
    Parameters
    ----------
    tfm : str
    qo : float array
    qs : float array
    """
    _libfcore.f90wrap_mwd_cost__discharge_tranformation(tfm=tfm, qo=qo, qs=qs)

def bayesian_compute_cost(self, mesh, input_data, parameters, output, options, \
    returns, interface_call=False):
    """
    bayesian_compute_cost(self, mesh, input_data, parameters, output, options, \
        returns)
    Defined at ../smash/fcore/cost/mwd_cost.f90 lines 72-127
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    parameters : Parametersdt
    output : Outputdt
    options : Optionsdt
    returns : Returnsdt
    """
    _libfcore.f90wrap_mwd_cost__bayesian_compute_cost(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, \
        parameters=parameters._handle, output=output._handle, \
        options=options._handle, returns=returns._handle)

def classical_compute_jobs(self, mesh, input_data, output, options, jobs, \
    interface_call=False):
    """
    classical_compute_jobs(self, mesh, input_data, output, options, jobs)
    Defined at ../smash/fcore/cost/mwd_cost.f90 lines 129-339
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    output : Outputdt
    options : Optionsdt
    jobs : float32
    """
    _libfcore.f90wrap_mwd_cost__classical_compute_jobs(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, output=output._handle, \
        options=options._handle, jobs=jobs)

def classical_compute_jreg(self, mesh, input_data, parameters, options, jreg, \
    interface_call=False):
    """
    classical_compute_jreg(self, mesh, input_data, parameters, options, jreg)
    Defined at ../smash/fcore/cost/mwd_cost.f90 lines 341-367
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    parameters : Parametersdt
    options : Optionsdt
    jreg : float32
    """
    _libfcore.f90wrap_mwd_cost__classical_compute_jreg(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, \
        parameters=parameters._handle, options=options._handle, jreg=jreg)

def classical_compute_cost(self, mesh, input_data, parameters, output, options, \
    returns, interface_call=False):
    """
    classical_compute_cost(self, mesh, input_data, parameters, output, options, \
        returns)
    Defined at ../smash/fcore/cost/mwd_cost.f90 lines 369-388
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    parameters : Parametersdt
    output : Outputdt
    options : Optionsdt
    returns : Returnsdt
    """
    _libfcore.f90wrap_mwd_cost__classical_compute_cost(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, \
        parameters=parameters._handle, output=output._handle, \
        options=options._handle, returns=returns._handle)

def compute_cost(self, mesh, input_data, parameters, output, options, returns, \
    interface_call=False):
    """
    compute_cost(self, mesh, input_data, parameters, output, options, returns)
    Defined at ../smash/fcore/cost/mwd_cost.f90 lines 390-403
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    parameters : Parametersdt
    output : Outputdt
    options : Optionsdt
    returns : Returnsdt
    """
    _libfcore.f90wrap_mwd_cost__compute_cost(setup=self._handle, mesh=mesh._handle, \
        input_data=input_data._handle, parameters=parameters._handle, \
        output=output._handle, options=options._handle, returns=returns._handle)


_array_initialisers = []
_dt_array_initialisers = []

try:
    for func in _array_initialisers:
        func()
except ValueError:
    logger.debug('unallocated array(s) detected on import of module "mwd_cost".')

for func in _dt_array_initialisers:
    func()
