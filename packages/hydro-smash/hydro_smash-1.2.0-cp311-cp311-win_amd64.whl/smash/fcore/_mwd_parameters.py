"""
(MWD) Module Wrapped and Differentiated.

Type
----

- ParametersDT
Container for all parameters. The goal is to keep the control vector in sync \
    with the spatial matrices
of rainfall-runoff parameters and the hyper parameters for mu/sigma of \
    structural erros

========================== =====================================
`Variables`                Description
========================== =====================================
``control``                ControlDT
``rr_parameters``          RR_ParametersDT
``rr_initial_states``      RR_StatesDT
``serr_mu_parameters``     SErr_Mu_ParametersDT
``serr_sigma_parameters``  SErr_Sigma_ParametersDT

Subroutine
----------

- ParametersDT_initialise
- ParametersDT_copy

Module mwd_parameters
Defined at ../smash/fcore/derived_type/mwd_parameters.f90 lines 24-59
"""
from __future__ import print_function, absolute_import, division
from smash.fcore import _libfcore
import f90wrap.runtime
import logging
import numpy
import warnings
import weakref
from smash.fcore._mwd_rr_states import RR_StatesDT
from smash.fcore._mwd_serr_sigma_parameters import SErr_Sigma_ParametersDT
from smash.fcore._mwd_serr_mu_parameters import SErr_Mu_ParametersDT
from smash.fcore._mwd_control import ControlDT
from smash.fcore._mwd_rr_parameters import RR_ParametersDT
from smash.fcore._mwd_nn_parameters import NN_ParametersDT

logger = logging.getLogger(__name__)
warnings.filterwarnings("error", category=numpy.exceptions.ComplexWarning)
_arrays = {}
_objs = {}

@f90wrap.runtime.register_class("libfcore.ParametersDT")
class ParametersDT(f90wrap.runtime.FortranDerivedType):
    """
    Type(name=parametersdt)
    Defined at ../smash/fcore/derived_type/mwd_parameters.f90 lines 35-41
    """
    def __init__(self, setup, mesh, handle=None):
        """
        only: sp
        only: SetupDT
        only: MeshDT
        only: ControlDT
        only: RR_ParametersDT, RR_ParametersDT_initialise
        only: RR_StatesDT, RR_StatesDT_initialise
        only: SErr_Mu_ParametersDT, SErr_Mu_ParametersDT_initialise
        only: SErr_Sigma_ParametersDT, SErr_Sigma_ParametersDT_initialise
        only: NN_ParametersDT, NN_ParametersDT_initialise
        
        self = Parametersdt(setup, mesh)
        Defined at ../smash/fcore/derived_type/mwd_parameters.f90 lines 44-53
        
        Parameters
        ----------
        setup : Setupdt
        mesh : Meshdt
        
        Returns
        -------
        this : Parametersdt
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num \
            == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = \
                _libfcore.f90wrap_mwd_parameters__parametersdt_initialise(setup=setup._handle, \
                mesh=mesh._handle)
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(_libfcore, "f90wrap_mwd_parameters__parametersdt_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    def copy(self, interface_call=False):
        """
        this_copy = parametersdt_copy(self)
        Defined at ../smash/fcore/derived_type/mwd_parameters.f90 lines 55-59
        
        Parameters
        ----------
        this : Parametersdt
        
        Returns
        -------
        this_copy : Parametersdt
        """
        this_copy = \
            _libfcore.f90wrap_mwd_parameters__parametersdt_copy(this=self._handle)
        this_copy = \
            f90wrap.runtime.lookup_class("libfcore.ParametersDT").from_handle(this_copy, \
            alloc=True)
        this_copy._setup_finalizer()
        return this_copy
    
    @property
    def control(self):
        """
        Element control ftype=type(controldt) pytype=Controldt
        Defined at ../smash/fcore/derived_type/mwd_parameters.f90 line 36
        """
        control_handle = _libfcore.f90wrap_parametersdt__get__control(self._handle)
        if tuple(control_handle) in self._objs:
            control = self._objs[tuple(control_handle)]
        else:
            control = ControlDT.from_handle(control_handle)
            self._objs[tuple(control_handle)] = control
        return control
    
    @control.setter
    def control(self, control):
        control = control._handle
        _libfcore.f90wrap_parametersdt__set__control(self._handle, control)
    
    @property
    def rr_parameters(self):
        """
        Element rr_parameters ftype=type(rr_parametersdt) pytype=Rr_Parametersdt
        Defined at ../smash/fcore/derived_type/mwd_parameters.f90 line 37
        """
        rr_parameters_handle = \
            _libfcore.f90wrap_parametersdt__get__rr_parameters(self._handle)
        if tuple(rr_parameters_handle) in self._objs:
            rr_parameters = self._objs[tuple(rr_parameters_handle)]
        else:
            rr_parameters = RR_ParametersDT.from_handle(rr_parameters_handle)
            self._objs[tuple(rr_parameters_handle)] = rr_parameters
        return rr_parameters
    
    @rr_parameters.setter
    def rr_parameters(self, rr_parameters):
        rr_parameters = rr_parameters._handle
        _libfcore.f90wrap_parametersdt__set__rr_parameters(self._handle, rr_parameters)
    
    @property
    def rr_initial_states(self):
        """
        Element rr_initial_states ftype=type(rr_statesdt) pytype=Rr_Statesdt
        Defined at ../smash/fcore/derived_type/mwd_parameters.f90 line 38
        """
        rr_initial_states_handle = \
            _libfcore.f90wrap_parametersdt__get__rr_initial_states(self._handle)
        if tuple(rr_initial_states_handle) in self._objs:
            rr_initial_states = self._objs[tuple(rr_initial_states_handle)]
        else:
            rr_initial_states = RR_StatesDT.from_handle(rr_initial_states_handle)
            self._objs[tuple(rr_initial_states_handle)] = rr_initial_states
        return rr_initial_states
    
    @rr_initial_states.setter
    def rr_initial_states(self, rr_initial_states):
        rr_initial_states = rr_initial_states._handle
        _libfcore.f90wrap_parametersdt__set__rr_initial_states(self._handle, \
            rr_initial_states)
    
    @property
    def serr_mu_parameters(self):
        """
        Element serr_mu_parameters ftype=type(serr_mu_parametersdt) \
            pytype=Serr_Mu_Parametersdt
        Defined at ../smash/fcore/derived_type/mwd_parameters.f90 line 39
        """
        serr_mu_parameters_handle = \
            _libfcore.f90wrap_parametersdt__get__serr_mu_parameters(self._handle)
        if tuple(serr_mu_parameters_handle) in self._objs:
            serr_mu_parameters = self._objs[tuple(serr_mu_parameters_handle)]
        else:
            serr_mu_parameters = SErr_Mu_ParametersDT.from_handle(serr_mu_parameters_handle)
            self._objs[tuple(serr_mu_parameters_handle)] = serr_mu_parameters
        return serr_mu_parameters
    
    @serr_mu_parameters.setter
    def serr_mu_parameters(self, serr_mu_parameters):
        serr_mu_parameters = serr_mu_parameters._handle
        _libfcore.f90wrap_parametersdt__set__serr_mu_parameters(self._handle, \
            serr_mu_parameters)
    
    @property
    def serr_sigma_parameters(self):
        """
        Element serr_sigma_parameters ftype=type(serr_sigma_parametersdt) \
            pytype=Serr_Sigma_Parametersdt
        Defined at ../smash/fcore/derived_type/mwd_parameters.f90 line 40
        """
        serr_sigma_parameters_handle = \
            _libfcore.f90wrap_parametersdt__get__serr_sigma_parameters(self._handle)
        if tuple(serr_sigma_parameters_handle) in self._objs:
            serr_sigma_parameters = self._objs[tuple(serr_sigma_parameters_handle)]
        else:
            serr_sigma_parameters = \
                SErr_Sigma_ParametersDT.from_handle(serr_sigma_parameters_handle)
            self._objs[tuple(serr_sigma_parameters_handle)] = serr_sigma_parameters
        return serr_sigma_parameters
    
    @serr_sigma_parameters.setter
    def serr_sigma_parameters(self, serr_sigma_parameters):
        serr_sigma_parameters = serr_sigma_parameters._handle
        _libfcore.f90wrap_parametersdt__set__serr_sigma_parameters(self._handle, \
            serr_sigma_parameters)
    
    @property
    def nn_parameters(self):
        """
        Element nn_parameters ftype=type(nn_parametersdt) pytype=Nn_Parametersdt
        Defined at ../smash/fcore/derived_type/mwd_parameters.f90 line 41
        """
        nn_parameters_handle = \
            _libfcore.f90wrap_parametersdt__get__nn_parameters(self._handle)
        if tuple(nn_parameters_handle) in self._objs:
            nn_parameters = self._objs[tuple(nn_parameters_handle)]
        else:
            nn_parameters = NN_ParametersDT.from_handle(nn_parameters_handle)
            self._objs[tuple(nn_parameters_handle)] = nn_parameters
        return nn_parameters
    
    @nn_parameters.setter
    def nn_parameters(self, nn_parameters):
        nn_parameters = nn_parameters._handle
        _libfcore.f90wrap_parametersdt__set__nn_parameters(self._handle, nn_parameters)
    
    
    def __repr__(self):
        ret = [self.__class__.__name__]
        for attr in dir(self):
            if attr.startswith("_"):
                continue
            try:
                value = getattr(self, attr)
            except Exception:
                continue
            if callable(value):
                continue
            elif isinstance(value, f90wrap.runtime.FortranDerivedTypeArray):
                n = len(value)
                nrepr = 4
                if n == 0:
                    continue
                else:
                    repr_value = [value[0].__class__.__name__] * min(n, nrepr)
                if n > nrepr:
                    repr_value.insert(2, "...")
                repr_value = repr(repr_value)
            else:
                repr_value = repr(value)
            ret.append(f"    {attr}: {repr_value}")
        return "\n".join(ret)
    
    
    _dt_array_initialisers = []
    


_array_initialisers = []
_dt_array_initialisers = []


try:
    for func in _array_initialisers:
        func()
except ValueError:
    logger.debug('unallocated array(s) detected on import of module \
        "mwd_parameters".')

for func in _dt_array_initialisers:
    func()
