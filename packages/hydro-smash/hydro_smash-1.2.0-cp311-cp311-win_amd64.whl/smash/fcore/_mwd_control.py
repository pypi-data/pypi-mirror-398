"""
(MWD) Module Wrapped and Differentiated.

Type
----

- ControlDT
Control vector used in optimize and quantities required by the optimizer

========================== =====================================
`Variables`                Description
========================== =====================================
``x``                      Control vector
``l``                      Control vector lower bound
``u``                      Control vector upper bound
``x_raw``                  Control vector raw
``l_raw``                  Control vector lower bound raw
``u_raw``                  Control vector upper bound raw
``nbd``                    Control vector kind of bound

Subroutine
----------

- ControlDT_initialise
- ControlDT_copy

Module mwd_control
Defined at ../smash/fcore/derived_type/mwd_control.f90 lines 25-91
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

@f90wrap.runtime.register_class("libfcore.ControlDT")
class ControlDT(f90wrap.runtime.FortranDerivedType):
    """
    Type(name=controldt)
    Defined at ../smash/fcore/derived_type/mwd_control.f90 lines 28-39
    """
    def __init__(self, nbk, handle=None):
        """
        only: sp
        
        self = Controldt(nbk)
        Defined at ../smash/fcore/derived_type/mwd_control.f90 lines 42-64
        
        Parameters
        ----------
        nbk : int array
        
        Returns
        -------
        this : Controldt
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num \
            == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = _libfcore.f90wrap_mwd_control__controldt_initialise(nbk=nbk)
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(_libfcore, "f90wrap_mwd_control__controldt_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    def copy(self, interface_call=False):
        """
        this_copy = controldt_copy(self)
        Defined at ../smash/fcore/derived_type/mwd_control.f90 lines 80-84
        
        Parameters
        ----------
        this : Controldt
        
        Returns
        -------
        this_copy : Controldt
        """
        this_copy = _libfcore.f90wrap_mwd_control__controldt_copy(this=self._handle)
        this_copy = \
            f90wrap.runtime.lookup_class("libfcore.ControlDT").from_handle(this_copy, \
            alloc=True)
        this_copy._setup_finalizer()
        return this_copy
    
    def dealloc(self, interface_call=False):
        """
        controldt_dealloc(self)
        Defined at ../smash/fcore/derived_type/mwd_control.f90 lines 88-91
        
        Parameters
        ----------
        this : Controldt
        """
        _libfcore.f90wrap_mwd_control__controldt_dealloc(this=self._handle)
    
    @property
    def n(self):
        """
        Element n ftype=integer  pytype=int32
        Defined at ../smash/fcore/derived_type/mwd_control.f90 line 29
        """
        return _libfcore.f90wrap_controldt__get__n(self._handle)
    
    @n.setter
    def n(self, n):
        _libfcore.f90wrap_controldt__set__n(self._handle, n)
    
    @property
    def nbk(self):
        """
        Element nbk ftype=integer pytype=int array
        Defined at ../smash/fcore/derived_type/mwd_control.f90 line 31
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_controldt__array__nbk(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        nbk = self._arrays.get(array_hash)
        if nbk is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if nbk.ctypes.data != array_handle:
                nbk = None
        if nbk is None:
            try:
                nbk = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_controldt__array__nbk)
            except TypeError:
                nbk = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = nbk
        return nbk
    
    @nbk.setter
    def nbk(self, nbk):
        self.nbk[...] = nbk
    
    @property
    def x(self):
        """
        Element x ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_control.f90 line 32
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_controldt__array__x(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        x = self._arrays.get(array_hash)
        if x is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if x.ctypes.data != array_handle:
                x = None
        if x is None:
            try:
                x = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_controldt__array__x)
            except TypeError:
                x = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = x
        return x
    
    @x.setter
    def x(self, x):
        self.x[...] = x
    
    @property
    def l(self):
        """
        Element l ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_control.f90 line 33
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_controldt__array__l(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        l = self._arrays.get(array_hash)
        if l is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if l.ctypes.data != array_handle:
                l = None
        if l is None:
            try:
                l = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_controldt__array__l)
            except TypeError:
                l = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = l
        return l
    
    @l.setter
    def l(self, l):
        self.l[...] = l
    
    @property
    def u(self):
        """
        Element u ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_control.f90 line 34
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_controldt__array__u(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        u = self._arrays.get(array_hash)
        if u is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if u.ctypes.data != array_handle:
                u = None
        if u is None:
            try:
                u = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_controldt__array__u)
            except TypeError:
                u = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = u
        return u
    
    @u.setter
    def u(self, u):
        self.u[...] = u
    
    @property
    def x_raw(self):
        """
        Element x_raw ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_control.f90 line 35
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_controldt__array__x_raw(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        x_raw = self._arrays.get(array_hash)
        if x_raw is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if x_raw.ctypes.data != array_handle:
                x_raw = None
        if x_raw is None:
            try:
                x_raw = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_controldt__array__x_raw)
            except TypeError:
                x_raw = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = x_raw
        return x_raw
    
    @x_raw.setter
    def x_raw(self, x_raw):
        self.x_raw[...] = x_raw
    
    @property
    def l_raw(self):
        """
        Element l_raw ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_control.f90 line 36
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_controldt__array__l_raw(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        l_raw = self._arrays.get(array_hash)
        if l_raw is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if l_raw.ctypes.data != array_handle:
                l_raw = None
        if l_raw is None:
            try:
                l_raw = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_controldt__array__l_raw)
            except TypeError:
                l_raw = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = l_raw
        return l_raw
    
    @l_raw.setter
    def l_raw(self, l_raw):
        self.l_raw[...] = l_raw
    
    @property
    def u_raw(self):
        """
        Element u_raw ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_control.f90 line 37
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_controldt__array__u_raw(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        u_raw = self._arrays.get(array_hash)
        if u_raw is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if u_raw.ctypes.data != array_handle:
                u_raw = None
        if u_raw is None:
            try:
                u_raw = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_controldt__array__u_raw)
            except TypeError:
                u_raw = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = u_raw
        return u_raw
    
    @u_raw.setter
    def u_raw(self, u_raw):
        self.u_raw[...] = u_raw
    
    @property
    def nbd(self):
        """
        Element nbd ftype=integer pytype=int array
        Defined at ../smash/fcore/derived_type/mwd_control.f90 line 38
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_controldt__array__nbd(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        nbd = self._arrays.get(array_hash)
        if nbd is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if nbd.ctypes.data != array_handle:
                nbd = None
        if nbd is None:
            try:
                nbd = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_controldt__array__nbd)
            except TypeError:
                nbd = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = nbd
        return nbd
    
    @nbd.setter
    def nbd(self, nbd):
        self.nbd[...] = nbd
    
    @property
    @f90wrap_getter_char_array
    def name(self):
        """
        Element name ftype=character(lchar) pytype=str array
        Defined at ../smash/fcore/derived_type/mwd_control.f90 line 39
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_controldt__array__name(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        name = self._arrays.get(array_hash)
        if name is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if name.ctypes.data != array_handle:
                name = None
        if name is None:
            try:
                name = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_controldt__array__name)
            except TypeError:
                name = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = name
        return name
    
    @name.setter
    @f90wrap_setter_char_array
    def name(self, name):
        self.name[...] = name
    
    
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
    logger.debug('unallocated array(s) detected on import of module "mwd_control".')

for func in _dt_array_initialisers:
    func()
