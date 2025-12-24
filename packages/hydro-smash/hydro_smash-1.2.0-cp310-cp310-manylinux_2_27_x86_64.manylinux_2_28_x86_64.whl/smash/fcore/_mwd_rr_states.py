"""
(MWD) Module Wrapped and Differentiated.

Type
----

- RR_StatesDT
Matrices containting spatialized states of hydrological operators.
(reservoir level ...) The matrices are updated at each time step.

========================== =====================================
`Variables`                Description
========================== =====================================
``keys``                   Rainfall-runoff states keys
``values``                 Rainfall-runoff states values

Subroutine
----------

- RR_StatesDT_initialise
- RR_StatesDT_copy

Module mwd_rr_states
Defined at ../smash/fcore/derived_type/mwd_rr_states.f90 lines 21-46
"""
from __future__ import print_function, absolute_import, division
from smash.fcore._f90wrap_decorator import f90wrap_getter_char_array, f90wrap_setter_char_array
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

@f90wrap.runtime.register_class("libfcore.RR_StatesDT")
class RR_StatesDT(f90wrap.runtime.FortranDerivedType):
    """
    Type(name=rr_statesdt)
    Defined at ../smash/fcore/derived_type/mwd_rr_states.f90 lines 26-28
    """
    def __init__(self, setup, mesh, handle=None):
        """
        Default states value will be handled in Python
        only: sp, lchar
        only: SetupDT
        only: MeshDT
        
        self = Rr_Statesdt(setup, mesh)
        Defined at ../smash/fcore/derived_type/mwd_rr_states.f90 lines 31-40
        
        Parameters
        ----------
        setup : Setupdt
        mesh : Meshdt
        
        Returns
        -------
        this : Rr_Statesdt
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num \
            == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = \
                _libfcore.f90wrap_mwd_rr_states__rr_statesdt_initialise(setup=setup._handle, \
                mesh=mesh._handle)
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(_libfcore, "f90wrap_mwd_rr_states__rr_statesdt_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    def copy(self, interface_call=False):
        """
        this_copy = rr_statesdt_copy(self)
        Defined at ../smash/fcore/derived_type/mwd_rr_states.f90 lines 42-46
        
        Parameters
        ----------
        this : Rr_Statesdt
        
        Returns
        -------
        this_copy : Rr_Statesdt
        """
        this_copy = _libfcore.f90wrap_mwd_rr_states__rr_statesdt_copy(this=self._handle)
        this_copy = \
            f90wrap.runtime.lookup_class("libfcore.RR_StatesDT").from_handle(this_copy, \
            alloc=True)
        this_copy._setup_finalizer()
        return this_copy
    
    @property
    @f90wrap_getter_char_array
    def keys(self):
        """
        Element keys ftype=character(lchar) pytype=str array
        Defined at ../smash/fcore/derived_type/mwd_rr_states.f90 line 27
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_rr_statesdt__array__keys(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        keys = self._arrays.get(array_hash)
        if keys is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if keys.ctypes.data != array_handle:
                keys = None
        if keys is None:
            try:
                keys = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_rr_statesdt__array__keys)
            except TypeError:
                keys = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = keys
        return keys
    
    @keys.setter
    @f90wrap_setter_char_array
    def keys(self, keys):
        self.keys[...] = keys
    
    @property
    def values(self):
        """
        Element values ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_rr_states.f90 line 28
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_rr_statesdt__array__values(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        values = self._arrays.get(array_hash)
        if values is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if values.ctypes.data != array_handle:
                values = None
        if values is None:
            try:
                values = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_rr_statesdt__array__values)
            except TypeError:
                values = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = values
        return values
    
    @values.setter
    def values(self, values):
        self.values[...] = values
    
    
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
        "mwd_rr_states".')

for func in _dt_array_initialisers:
    func()
