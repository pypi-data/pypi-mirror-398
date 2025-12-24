"""
(MWD) Module Wrapped and Differentiated.

Type
----

- Sparse_MatrixDT
Sparse matrices handling atmospheric data(prcp, pet, snow ...)
See COO matrices(google, scipy)

======================== =======================================
`Variables`              Description
======================== =======================================
``n``                    Number of data stored
``coo_fmt``              Sparse Matrix in COO format(default: .true.)
``zvalue``               Non stored value(default: 0)
``indices``              Indices of the sparse matrix
``values``               Values of the sparse matrix
======================== =======================================

Subroutine
----------

- Sparse_MatrixDT_initialise
- Sparse_MatrixDT_copy

Module mwd_sparse_matrix
Defined at ../smash/fcore/derived_type/mwd_sparse_matrix.f90 lines 25-84
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

@f90wrap.runtime.register_class("libfcore.Sparse_MatrixDT")
class Sparse_MatrixDT(f90wrap.runtime.FortranDerivedType):
    """
    Type(name=sparse_matrixdt)
    Defined at ../smash/fcore/derived_type/mwd_sparse_matrix.f90 lines 28-33
    """
    def __init__(self, n, coo_fmt, zvalue, handle=None):
        """
        only: sp
        
        self = Sparse_Matrixdt(n, coo_fmt, zvalue)
        Defined at ../smash/fcore/derived_type/mwd_sparse_matrix.f90 lines 36-51
        
        Parameters
        ----------
        n : int32
        coo_fmt : bool
        zvalue : float32
        
        Returns
        -------
        this : Sparse_Matrixdt
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num \
            == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = _libfcore.f90wrap_mwd_sparse_matrix__sparse_matrixdt_initialise(n=n, \
                coo_fmt=coo_fmt, zvalue=zvalue)
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(_libfcore, \
                "f90wrap_mwd_sparse_matrix__sparse_matrixdt_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    def alloc(self, n, coo_fmt, zvalue, interface_call=False):
        """
        sparse_matrixdt_alloc(self, n, coo_fmt, zvalue)
        Defined at ../smash/fcore/derived_type/mwd_sparse_matrix.f90 lines 72-78
        
        Parameters
        ----------
        this : Sparse_Matrixdt
        n : int32
        coo_fmt : bool
        zvalue : float32
        """
        _libfcore.f90wrap_mwd_sparse_matrix__sparse_matrixdt_alloc(this=self._handle, \
            n=n, coo_fmt=coo_fmt, zvalue=zvalue)
    
    def copy(self, this_copy, interface_call=False):
        """
        sparse_matrixdt_copy(self, this_copy)
        Defined at ../smash/fcore/derived_type/mwd_sparse_matrix.f90 lines 80-84
        
        Parameters
        ----------
        this : Sparse_Matrixdt
        this_copy : Sparse_Matrixdt
        """
        _libfcore.f90wrap_mwd_sparse_matrix__sparse_matrixdt_copy(this=self._handle, \
            this_copy=this_copy._handle)
    
    @property
    def n(self):
        """
        Element n ftype=integer  pytype=int32
        Defined at ../smash/fcore/derived_type/mwd_sparse_matrix.f90 line 29
        """
        return _libfcore.f90wrap_sparse_matrixdt__get__n(self._handle)
    
    @n.setter
    def n(self, n):
        _libfcore.f90wrap_sparse_matrixdt__set__n(self._handle, n)
    
    @property
    def coo_fmt(self):
        """
        Element coo_fmt ftype=logical pytype=bool
        Defined at ../smash/fcore/derived_type/mwd_sparse_matrix.f90 line 30
        """
        return _libfcore.f90wrap_sparse_matrixdt__get__coo_fmt(self._handle)
    
    @coo_fmt.setter
    def coo_fmt(self, coo_fmt):
        _libfcore.f90wrap_sparse_matrixdt__set__coo_fmt(self._handle, coo_fmt)
    
    @property
    def zvalue(self):
        """
        Element zvalue ftype=real(sp) pytype=float32
        Defined at ../smash/fcore/derived_type/mwd_sparse_matrix.f90 line 31
        """
        return _libfcore.f90wrap_sparse_matrixdt__get__zvalue(self._handle)
    
    @zvalue.setter
    def zvalue(self, zvalue):
        _libfcore.f90wrap_sparse_matrixdt__set__zvalue(self._handle, zvalue)
    
    @property
    def indices(self):
        """
        Element indices ftype=integer pytype=int array
        Defined at ../smash/fcore/derived_type/mwd_sparse_matrix.f90 line 32
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_sparse_matrixdt__array__indices(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        indices = self._arrays.get(array_hash)
        if indices is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if indices.ctypes.data != array_handle:
                indices = None
        if indices is None:
            try:
                indices = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_sparse_matrixdt__array__indices)
            except TypeError:
                indices = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = indices
        return indices
    
    @indices.setter
    def indices(self, indices):
        self.indices[...] = indices
    
    @property
    def values(self):
        """
        Element values ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_sparse_matrix.f90 line 33
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_sparse_matrixdt__array__values(self._handle)
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
                                        _libfcore.f90wrap_sparse_matrixdt__array__values)
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
        "mwd_sparse_matrix".')

for func in _dt_array_initialisers:
    func()
