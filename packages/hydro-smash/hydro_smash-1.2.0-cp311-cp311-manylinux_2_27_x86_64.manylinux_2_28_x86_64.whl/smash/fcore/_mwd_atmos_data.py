"""
(MWD) Module Wrapped and Differentiated.

Type
----

- Atmos_DataDT
Atmospheric data used to force smash and derived quantities.

======================== =======================================
`Variables`              Description
======================== =======================================
``prcp``                 Precipitation field                         [mm]
``pet``                  Potential evapotranspiration field          [mm]
``snow``                 Snow field                                  [mm]
``temp``                 Temperature field                           [C]
``sparse_prcp``          Sparse precipitation field                  [mm]
``sparse_pet``           Sparse potential evapotranspiration field   [mm]
``sparse_snow``          Sparse snow field                           [mm]
``sparse_temp``          Sparse temperature field                    [C]
``mean_prcp``            Mean precipitation at gauge                 [mm]
``mean_pet``             Mean potential evapotranspiration at gauge  [mm]
``mean_snow``            Mean snow at gauge                          [mm]
``mean_temp``            Mean temperature at gauge                   [C]
======================== =======================================

Subroutine
----------

- Atmos_DataDT_initialise
- Atmos_DataDT_copy

Module mwd_atmos_data
Defined at ../smash/fcore/derived_type/mwd_atmos_data.f90 lines 31-95
"""
from __future__ import print_function, absolute_import, division
from smash.fcore import _libfcore
import f90wrap.runtime
import logging
import numpy
import warnings
import weakref
from smash.fcore._mwd_sparse_matrix import Sparse_MatrixDT

logger = logging.getLogger(__name__)
warnings.filterwarnings("error", category=numpy.exceptions.ComplexWarning)
_arrays = {}
_objs = {}

@f90wrap.runtime.register_class("libfcore.Atmos_DataDT")
class Atmos_DataDT(f90wrap.runtime.FortranDerivedType):
    """
    Type(name=atmos_datadt)
    Defined at ../smash/fcore/derived_type/mwd_atmos_data.f90 lines 37-49
    """
    def __init__(self, setup, mesh, handle=None):
        """
        only: sp
        only: SetupDT
        only: MeshDT
        only: Sparse_MatrixDT, Sparse_MatrixDT_initialise_array
        
        self = Atmos_Datadt(setup, mesh)
        Defined at ../smash/fcore/derived_type/mwd_atmos_data.f90 lines 52-89
        
        Parameters
        ----------
        setup : Setupdt
        mesh : Meshdt
        
        Returns
        -------
        this : Atmos_Datadt
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num \
            == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = \
                _libfcore.f90wrap_mwd_atmos_data__atmos_datadt_initialise(setup=setup._handle, \
                mesh=mesh._handle)
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(_libfcore, "f90wrap_mwd_atmos_data__atmos_datadt_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    def copy(self, interface_call=False):
        """
        this_copy = atmos_datadt_copy(self)
        Defined at ../smash/fcore/derived_type/mwd_atmos_data.f90 lines 91-95
        
        Parameters
        ----------
        this : Atmos_Datadt
        
        Returns
        -------
        this_copy : Atmos_Datadt
        """
        this_copy = \
            _libfcore.f90wrap_mwd_atmos_data__atmos_datadt_copy(this=self._handle)
        this_copy = \
            f90wrap.runtime.lookup_class("libfcore.Atmos_DataDT").from_handle(this_copy, \
            alloc=True)
        this_copy._setup_finalizer()
        return this_copy
    
    @property
    def prcp(self):
        """
        Element prcp ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_atmos_data.f90 line 38
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_atmos_datadt__array__prcp(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        prcp = self._arrays.get(array_hash)
        if prcp is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if prcp.ctypes.data != array_handle:
                prcp = None
        if prcp is None:
            try:
                prcp = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_atmos_datadt__array__prcp)
            except TypeError:
                prcp = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = prcp
        return prcp
    
    @prcp.setter
    def prcp(self, prcp):
        self.prcp[...] = prcp
    
    @property
    def pet(self):
        """
        Element pet ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_atmos_data.f90 line 39
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_atmos_datadt__array__pet(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        pet = self._arrays.get(array_hash)
        if pet is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if pet.ctypes.data != array_handle:
                pet = None
        if pet is None:
            try:
                pet = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_atmos_datadt__array__pet)
            except TypeError:
                pet = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = pet
        return pet
    
    @pet.setter
    def pet(self, pet):
        self.pet[...] = pet
    
    @property
    def snow(self):
        """
        Element snow ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_atmos_data.f90 line 40
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_atmos_datadt__array__snow(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        snow = self._arrays.get(array_hash)
        if snow is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if snow.ctypes.data != array_handle:
                snow = None
        if snow is None:
            try:
                snow = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_atmos_datadt__array__snow)
            except TypeError:
                snow = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = snow
        return snow
    
    @snow.setter
    def snow(self, snow):
        self.snow[...] = snow
    
    @property
    def temp(self):
        """
        Element temp ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_atmos_data.f90 line 41
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_atmos_datadt__array__temp(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        temp = self._arrays.get(array_hash)
        if temp is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if temp.ctypes.data != array_handle:
                temp = None
        if temp is None:
            try:
                temp = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_atmos_datadt__array__temp)
            except TypeError:
                temp = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = temp
        return temp
    
    @temp.setter
    def temp(self, temp):
        self.temp[...] = temp
    
    def init_array_sparse_prcp(self):
        self.sparse_prcp = f90wrap.runtime.FortranDerivedTypeArray(self,
                                            _libfcore.f90wrap_atmos_datadt__array_getitem__sparse_prcp,
                                            _libfcore.f90wrap_atmos_datadt__array_setitem__sparse_prcp,
                                            _libfcore.f90wrap_atmos_datadt__array_len__sparse_prcp,
                                            """
        Element sparse_prcp ftype=type(sparse_matrixdt) pytype=Sparse_Matrixdt array
        Defined at ../smash/fcore/derived_type/mwd_atmos_data.f90 line 42
        """, Sparse_MatrixDT,
                                            module_level=False)
        return self.sparse_prcp
    
    def init_array_sparse_pet(self):
        self.sparse_pet = f90wrap.runtime.FortranDerivedTypeArray(self,
                                            _libfcore.f90wrap_atmos_datadt__array_getitem__sparse_pet,
                                            _libfcore.f90wrap_atmos_datadt__array_setitem__sparse_pet,
                                            _libfcore.f90wrap_atmos_datadt__array_len__sparse_pet,
                                            """
        Element sparse_pet ftype=type(sparse_matrixdt) pytype=Sparse_Matrixdt array
        Defined at ../smash/fcore/derived_type/mwd_atmos_data.f90 line 43
        """, Sparse_MatrixDT,
                                            module_level=False)
        return self.sparse_pet
    
    def init_array_sparse_snow(self):
        self.sparse_snow = f90wrap.runtime.FortranDerivedTypeArray(self,
                                            _libfcore.f90wrap_atmos_datadt__array_getitem__sparse_snow,
                                            _libfcore.f90wrap_atmos_datadt__array_setitem__sparse_snow,
                                            _libfcore.f90wrap_atmos_datadt__array_len__sparse_snow,
                                            """
        Element sparse_snow ftype=type(sparse_matrixdt) pytype=Sparse_Matrixdt array
        Defined at ../smash/fcore/derived_type/mwd_atmos_data.f90 line 44
        """, Sparse_MatrixDT,
                                            module_level=False)
        return self.sparse_snow
    
    def init_array_sparse_temp(self):
        self.sparse_temp = f90wrap.runtime.FortranDerivedTypeArray(self,
                                            _libfcore.f90wrap_atmos_datadt__array_getitem__sparse_temp,
                                            _libfcore.f90wrap_atmos_datadt__array_setitem__sparse_temp,
                                            _libfcore.f90wrap_atmos_datadt__array_len__sparse_temp,
                                            """
        Element sparse_temp ftype=type(sparse_matrixdt) pytype=Sparse_Matrixdt array
        Defined at ../smash/fcore/derived_type/mwd_atmos_data.f90 line 45
        """, Sparse_MatrixDT,
                                            module_level=False)
        return self.sparse_temp
    
    @property
    def mean_prcp(self):
        """
        Element mean_prcp ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_atmos_data.f90 line 46
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_atmos_datadt__array__mean_prcp(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        mean_prcp = self._arrays.get(array_hash)
        if mean_prcp is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if mean_prcp.ctypes.data != array_handle:
                mean_prcp = None
        if mean_prcp is None:
            try:
                mean_prcp = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_atmos_datadt__array__mean_prcp)
            except TypeError:
                mean_prcp = f90wrap.runtime.direct_c_array(array_type, array_shape, \
                    array_handle)
            self._arrays[array_hash] = mean_prcp
        return mean_prcp
    
    @mean_prcp.setter
    def mean_prcp(self, mean_prcp):
        self.mean_prcp[...] = mean_prcp
    
    @property
    def mean_pet(self):
        """
        Element mean_pet ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_atmos_data.f90 line 47
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_atmos_datadt__array__mean_pet(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        mean_pet = self._arrays.get(array_hash)
        if mean_pet is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if mean_pet.ctypes.data != array_handle:
                mean_pet = None
        if mean_pet is None:
            try:
                mean_pet = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_atmos_datadt__array__mean_pet)
            except TypeError:
                mean_pet = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = mean_pet
        return mean_pet
    
    @mean_pet.setter
    def mean_pet(self, mean_pet):
        self.mean_pet[...] = mean_pet
    
    @property
    def mean_snow(self):
        """
        Element mean_snow ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_atmos_data.f90 line 48
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_atmos_datadt__array__mean_snow(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        mean_snow = self._arrays.get(array_hash)
        if mean_snow is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if mean_snow.ctypes.data != array_handle:
                mean_snow = None
        if mean_snow is None:
            try:
                mean_snow = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_atmos_datadt__array__mean_snow)
            except TypeError:
                mean_snow = f90wrap.runtime.direct_c_array(array_type, array_shape, \
                    array_handle)
            self._arrays[array_hash] = mean_snow
        return mean_snow
    
    @mean_snow.setter
    def mean_snow(self, mean_snow):
        self.mean_snow[...] = mean_snow
    
    @property
    def mean_temp(self):
        """
        Element mean_temp ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_atmos_data.f90 line 49
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_atmos_datadt__array__mean_temp(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        mean_temp = self._arrays.get(array_hash)
        if mean_temp is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if mean_temp.ctypes.data != array_handle:
                mean_temp = None
        if mean_temp is None:
            try:
                mean_temp = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_atmos_datadt__array__mean_temp)
            except TypeError:
                mean_temp = f90wrap.runtime.direct_c_array(array_type, array_shape, \
                    array_handle)
            self._arrays[array_hash] = mean_temp
        return mean_temp
    
    @mean_temp.setter
    def mean_temp(self, mean_temp):
        self.mean_temp[...] = mean_temp
    
    
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
    
    
    _dt_array_initialisers = [init_array_sparse_prcp, init_array_sparse_pet, \
        init_array_sparse_snow, init_array_sparse_temp]
    


_array_initialisers = []
_dt_array_initialisers = []


try:
    for func in _array_initialisers:
        func()
except ValueError:
    logger.debug('unallocated array(s) detected on import of module \
        "mwd_atmos_data".')

for func in _dt_array_initialisers:
    func()
