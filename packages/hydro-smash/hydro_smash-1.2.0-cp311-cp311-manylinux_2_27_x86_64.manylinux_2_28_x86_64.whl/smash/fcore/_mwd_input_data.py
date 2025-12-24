"""
(MWD) Module Wrapped and Differentiated.

Type
----

- Input_DataDT
Container for all user input data(not only forcing data but all inputs
needed to run and/or optimize the model). This data are not meant to be
changed at runtime once read.

======================== =======================================
`Variables`              Description
======================== =======================================
``response_data``        Response_DataDT
``u_response_data``      U_Response_DataDT
``physio_data``          Physio_DataDT
``atmos_data``           Atmos_DataDT
======================== =======================================

Subroutine
----------

- Input_DataDT_initialise
- Input_DataDT_copy

Module mwd_input_data
Defined at ../smash/fcore/derived_type/mwd_input_data.f90 lines 25-55
"""
from __future__ import print_function, absolute_import, division
from smash.fcore import _libfcore
import f90wrap.runtime
import logging
import numpy
import warnings
import weakref
from smash.fcore._mwd_physio_data import Physio_DataDT
from smash.fcore._mwd_u_response_data import U_Response_DataDT
from smash.fcore._mwd_atmos_data import Atmos_DataDT
from smash.fcore._mwd_response_data import Response_DataDT

logger = logging.getLogger(__name__)
warnings.filterwarnings("error", category=numpy.exceptions.ComplexWarning)
_arrays = {}
_objs = {}

@f90wrap.runtime.register_class("libfcore.Input_DataDT")
class Input_DataDT(f90wrap.runtime.FortranDerivedType):
    """
    Type(name=input_datadt)
    Defined at ../smash/fcore/derived_type/mwd_input_data.f90 lines 34-38
    """
    def __init__(self, setup, mesh, handle=None):
        """
        only: sp
        only: SetupDT
        only: MeshDT
        : only: ResponseDataDT, ResponseDataDT_initialise
        : only: U_ResponseDataDT, U_ResponseDataDT_initialise
        : only: Physio_DataDT, Physio_DataDT_initialise
        : only: Atmos_DataDT, Atmos_DataDT_initialise
        
        self = Input_Datadt(setup, mesh)
        Defined at ../smash/fcore/derived_type/mwd_input_data.f90 lines 41-49
        
        Parameters
        ----------
        setup : Setupdt
        mesh : Meshdt
        
        Returns
        -------
        this : Input_Datadt
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num \
            == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = \
                _libfcore.f90wrap_mwd_input_data__input_datadt_initialise(setup=setup._handle, \
                mesh=mesh._handle)
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(_libfcore, "f90wrap_mwd_input_data__input_datadt_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    def copy(self, interface_call=False):
        """
        this_copy = input_datadt_copy(self)
        Defined at ../smash/fcore/derived_type/mwd_input_data.f90 lines 51-55
        
        Parameters
        ----------
        this : Input_Datadt
        
        Returns
        -------
        this_copy : Input_Datadt
        """
        this_copy = \
            _libfcore.f90wrap_mwd_input_data__input_datadt_copy(this=self._handle)
        this_copy = \
            f90wrap.runtime.lookup_class("libfcore.Input_DataDT").from_handle(this_copy, \
            alloc=True)
        this_copy._setup_finalizer()
        return this_copy
    
    @property
    def response_data(self):
        """
        Element response_data ftype=type(response_datadt) pytype=Response_Datadt
        Defined at ../smash/fcore/derived_type/mwd_input_data.f90 line 35
        """
        response_data_handle = \
            _libfcore.f90wrap_input_datadt__get__response_data(self._handle)
        if tuple(response_data_handle) in self._objs:
            response_data = self._objs[tuple(response_data_handle)]
        else:
            response_data = Response_DataDT.from_handle(response_data_handle)
            self._objs[tuple(response_data_handle)] = response_data
        return response_data
    
    @response_data.setter
    def response_data(self, response_data):
        response_data = response_data._handle
        _libfcore.f90wrap_input_datadt__set__response_data(self._handle, response_data)
    
    @property
    def u_response_data(self):
        """
        Element u_response_data ftype=type(u_response_datadt) pytype=U_Response_Datadt
        Defined at ../smash/fcore/derived_type/mwd_input_data.f90 line 36
        """
        u_response_data_handle = \
            _libfcore.f90wrap_input_datadt__get__u_response_data(self._handle)
        if tuple(u_response_data_handle) in self._objs:
            u_response_data = self._objs[tuple(u_response_data_handle)]
        else:
            u_response_data = U_Response_DataDT.from_handle(u_response_data_handle)
            self._objs[tuple(u_response_data_handle)] = u_response_data
        return u_response_data
    
    @u_response_data.setter
    def u_response_data(self, u_response_data):
        u_response_data = u_response_data._handle
        _libfcore.f90wrap_input_datadt__set__u_response_data(self._handle, \
            u_response_data)
    
    @property
    def physio_data(self):
        """
        Element physio_data ftype=type(physio_datadt) pytype=Physio_Datadt
        Defined at ../smash/fcore/derived_type/mwd_input_data.f90 line 37
        """
        physio_data_handle = \
            _libfcore.f90wrap_input_datadt__get__physio_data(self._handle)
        if tuple(physio_data_handle) in self._objs:
            physio_data = self._objs[tuple(physio_data_handle)]
        else:
            physio_data = Physio_DataDT.from_handle(physio_data_handle)
            self._objs[tuple(physio_data_handle)] = physio_data
        return physio_data
    
    @physio_data.setter
    def physio_data(self, physio_data):
        physio_data = physio_data._handle
        _libfcore.f90wrap_input_datadt__set__physio_data(self._handle, physio_data)
    
    @property
    def atmos_data(self):
        """
        Element atmos_data ftype=type(atmos_datadt) pytype=Atmos_Datadt
        Defined at ../smash/fcore/derived_type/mwd_input_data.f90 line 38
        """
        atmos_data_handle = \
            _libfcore.f90wrap_input_datadt__get__atmos_data(self._handle)
        if tuple(atmos_data_handle) in self._objs:
            atmos_data = self._objs[tuple(atmos_data_handle)]
        else:
            atmos_data = Atmos_DataDT.from_handle(atmos_data_handle)
            self._objs[tuple(atmos_data_handle)] = atmos_data
        return atmos_data
    
    @atmos_data.setter
    def atmos_data(self, atmos_data):
        atmos_data = atmos_data._handle
        _libfcore.f90wrap_input_datadt__set__atmos_data(self._handle, atmos_data)
    
    
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
        "mwd_input_data".')

for func in _dt_array_initialisers:
    func()
