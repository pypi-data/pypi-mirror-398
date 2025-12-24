"""
(MW) Module Wrapped.

Subroutine
----------

- forward_run
- forward_run_d
- forward_run_b
- multiple_forward_run_sample_to_parameters
- multiple_forward_run

Module mw_forward
Defined at ../smash/fcore/forward/mw_forward.f90 lines 11-126
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

def forward_run(self, mesh, input_data, parameters, output, options, returns, \
    interface_call=False):
    """
    forward_run(self, mesh, input_data, parameters, output, options, returns)
    Defined at ../smash/fcore/forward/mw_forward.f90 lines 23-32
    
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
    _libfcore.f90wrap_mw_forward__forward_run(setup=self._handle, mesh=mesh._handle, \
        input_data=input_data._handle, parameters=parameters._handle, \
        output=output._handle, options=options._handle, returns=returns._handle)

def forward_run_d(self, mesh, input_data, parameters, parameters_d, output, \
    output_d, options, returns, interface_call=False):
    """
    forward_run_d(self, mesh, input_data, parameters, parameters_d, output, \
        output_d, options, returns)
    Defined at ../smash/fcore/forward/mw_forward.f90 lines 34-43
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    parameters : Parametersdt
    parameters_d : Parametersdt
    output : Outputdt
    output_d : Outputdt
    options : Optionsdt
    returns : Returnsdt
    """
    _libfcore.f90wrap_mw_forward__forward_run_d(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, \
        parameters=parameters._handle, parameters_d=parameters_d._handle, \
        output=output._handle, output_d=output_d._handle, options=options._handle, \
        returns=returns._handle)

def forward_run_b(self, mesh, input_data, parameters, parameters_b, output, \
    output_b, options, returns, interface_call=False):
    """
    forward_run_b(self, mesh, input_data, parameters, parameters_b, output, \
        output_b, options, returns)
    Defined at ../smash/fcore/forward/mw_forward.f90 lines 45-54
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    parameters : Parametersdt
    parameters_b : Parametersdt
    output : Outputdt
    output_b : Outputdt
    options : Optionsdt
    returns : Returnsdt
    """
    _libfcore.f90wrap_mw_forward__forward_run_b(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, \
        parameters=parameters._handle, parameters_b=parameters_b._handle, \
        output=output._handle, output_b=output_b._handle, options=options._handle, \
        returns=returns._handle)

def multiple_forward_run_sample_to_parameters(sample, samples_kind, samples_ind, \
    parameters, interface_call=False):
    """
    multiple_forward_run_sample_to_parameters(sample, samples_kind, samples_ind, \
        parameters)
    Defined at ../smash/fcore/forward/mw_forward.f90 lines 56-72
    
    Parameters
    ----------
    sample : float array
    samples_kind : int array
    samples_ind : int array
    parameters : Parametersdt
    """
    _libfcore.f90wrap_mw_forward__multiple_forward_run_sample_to_parameters(sample=sample, \
        samples_kind=samples_kind, samples_ind=samples_ind, \
        parameters=parameters._handle)

def multiple_forward_run(self, mesh, input_data, parameters, output, options, \
    samples, samples_kind, samples_ind, cost, q, interface_call=False):
    """
    multiple_forward_run(self, mesh, input_data, parameters, output, options, \
        samples, samples_kind, samples_ind, cost, q)
    Defined at ../smash/fcore/forward/mw_forward.f90 lines 74-126
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    parameters : Parametersdt
    output : Outputdt
    options : Optionsdt
    samples : float array
    samples_kind : int array
    samples_ind : int array
    cost : float array
    q : float array
    """
    _libfcore.f90wrap_mw_forward__multiple_forward_run(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, \
        parameters=parameters._handle, output=output._handle, \
        options=options._handle, samples=samples, samples_kind=samples_kind, \
        samples_ind=samples_ind, cost=cost, q=q)


_array_initialisers = []
_dt_array_initialisers = []

try:
    for func in _array_initialisers:
        func()
except ValueError:
    logger.debug('unallocated array(s) detected on import of module "mw_forward".')

for func in _dt_array_initialisers:
    func()
