"""
(MWD) Module Wrapped and Differentiated.

Type
----

- ResponseDT
Response simulated by the hydrological model.

======================== =======================================
`Variables`              Description
======================== =======================================
``q``                    Simulated discharge at gauges              [m3/s]
======================== =======================================

Subroutine
----------

- ResponseDT_initialise
- ResponseDT_copy

Module mwd_response
Defined at ../smash/fcore/derived_type/mwd_response.f90 lines 20-41
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

@f90wrap.runtime.register_class("libfcore.ResponseDT")
class ResponseDT(f90wrap.runtime.FortranDerivedType):
    """
    Type(name=responsedt)
    Defined at ../smash/fcore/derived_type/mwd_response.f90 lines 25-26
    """
    def __init__(self, setup, mesh, handle=None):
        """
        only: sp
        only: SetupDT
        only: MeshDT
        
        self = Responsedt(setup, mesh)
        Defined at ../smash/fcore/derived_type/mwd_response.f90 lines 29-35
        
        Parameters
        ----------
        setup : Setupdt
        mesh : Meshdt
        
        Returns
        -------
        this : Responsedt
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num \
            == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = \
                _libfcore.f90wrap_mwd_response__responsedt_initialise(setup=setup._handle, \
                mesh=mesh._handle)
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(_libfcore, "f90wrap_mwd_response__responsedt_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    def copy(self, interface_call=False):
        """
        this_copy = responsedt_copy(self)
        Defined at ../smash/fcore/derived_type/mwd_response.f90 lines 37-41
        
        Parameters
        ----------
        this : Responsedt
        
        Returns
        -------
        this_copy : Responsedt
        """
        this_copy = _libfcore.f90wrap_mwd_response__responsedt_copy(this=self._handle)
        this_copy = \
            f90wrap.runtime.lookup_class("libfcore.ResponseDT").from_handle(this_copy, \
            alloc=True)
        this_copy._setup_finalizer()
        return this_copy
    
    @property
    def q(self):
        """
        Element q ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_response.f90 line 26
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_responsedt__array__q(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        q = self._arrays.get(array_hash)
        if q is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if q.ctypes.data != array_handle:
                q = None
        if q is None:
            try:
                q = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_responsedt__array__q)
            except TypeError:
                q = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = q
        return q
    
    @q.setter
    def q(self, q):
        self.q[...] = q
    
    
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
        "mwd_response".')

for func in _dt_array_initialisers:
    func()
