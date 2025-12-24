"""
(MWD) Module Wrapped and Differentiated.

Type
----

- Physio_DataDT
Physiographic data used to force the regionalization, among other things.

======================== =======================================
`Variables`              Description
======================== =======================================
``descriptor`` Descriptor maps field [(descriptor dependent)]
``imperviousness``       Imperviousness map
``l_descriptor`` Descriptor maps field min value [(descriptor dependent)]
``u_descriptor`` Descriptor maps field max value [(descriptor dependent)]
======================== =======================================

Subroutine
----------

- Physio_DataDT_initialise
- Physio_DataDT_copy

Module mwd_physio_data
Defined at ../smash/fcore/derived_type/mwd_physio_data.f90 lines 23-53
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

@f90wrap.runtime.register_class("libfcore.Physio_DataDT")
class Physio_DataDT(f90wrap.runtime.FortranDerivedType):
    """
    Type(name=physio_datadt)
    Defined at ../smash/fcore/derived_type/mwd_physio_data.f90 lines 28-32
    """
    def __init__(self, setup, mesh, handle=None):
        """
        only: sp
        only: SetupDT
        only: MeshDT
        
        self = Physio_Datadt(setup, mesh)
        Defined at ../smash/fcore/derived_type/mwd_physio_data.f90 lines 35-47
        
        Parameters
        ----------
        setup : Setupdt
        mesh : Meshdt
        
        Returns
        -------
        this : Physio_Datadt
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num \
            == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = \
                _libfcore.f90wrap_mwd_physio_data__physio_datadt_initialise(setup=setup._handle, \
                mesh=mesh._handle)
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(_libfcore, \
                "f90wrap_mwd_physio_data__physio_datadt_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    def copy(self, interface_call=False):
        """
        this_copy = physio_datadt_copy(self)
        Defined at ../smash/fcore/derived_type/mwd_physio_data.f90 lines 49-53
        
        Parameters
        ----------
        this : Physio_Datadt
        
        Returns
        -------
        this_copy : Physio_Datadt
        """
        this_copy = \
            _libfcore.f90wrap_mwd_physio_data__physio_datadt_copy(this=self._handle)
        this_copy = \
            f90wrap.runtime.lookup_class("libfcore.Physio_DataDT").from_handle(this_copy, \
            alloc=True)
        this_copy._setup_finalizer()
        return this_copy
    
    @property
    def descriptor(self):
        """
        Element descriptor ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_physio_data.f90 line 29
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_physio_datadt__array__descriptor(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        descriptor = self._arrays.get(array_hash)
        if descriptor is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if descriptor.ctypes.data != array_handle:
                descriptor = None
        if descriptor is None:
            try:
                descriptor = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_physio_datadt__array__descriptor)
            except TypeError:
                descriptor = f90wrap.runtime.direct_c_array(array_type, array_shape, \
                    array_handle)
            self._arrays[array_hash] = descriptor
        return descriptor
    
    @descriptor.setter
    def descriptor(self, descriptor):
        self.descriptor[...] = descriptor
    
    @property
    def imperviousness(self):
        """
        Element imperviousness ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_physio_data.f90 line 30
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_physio_datadt__array__imperviousness(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        imperviousness = self._arrays.get(array_hash)
        if imperviousness is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if imperviousness.ctypes.data != array_handle:
                imperviousness = None
        if imperviousness is None:
            try:
                imperviousness = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_physio_datadt__array__imperviousness)
            except TypeError:
                imperviousness = f90wrap.runtime.direct_c_array(array_type, array_shape, \
                    array_handle)
            self._arrays[array_hash] = imperviousness
        return imperviousness
    
    @imperviousness.setter
    def imperviousness(self, imperviousness):
        self.imperviousness[...] = imperviousness
    
    @property
    def l_descriptor(self):
        """
        Element l_descriptor ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_physio_data.f90 line 31
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_physio_datadt__array__l_descriptor(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        l_descriptor = self._arrays.get(array_hash)
        if l_descriptor is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if l_descriptor.ctypes.data != array_handle:
                l_descriptor = None
        if l_descriptor is None:
            try:
                l_descriptor = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_physio_datadt__array__l_descriptor)
            except TypeError:
                l_descriptor = f90wrap.runtime.direct_c_array(array_type, array_shape, \
                    array_handle)
            self._arrays[array_hash] = l_descriptor
        return l_descriptor
    
    @l_descriptor.setter
    def l_descriptor(self, l_descriptor):
        self.l_descriptor[...] = l_descriptor
    
    @property
    def u_descriptor(self):
        """
        Element u_descriptor ftype=real(sp) pytype=float array
        Defined at ../smash/fcore/derived_type/mwd_physio_data.f90 line 32
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_physio_datadt__array__u_descriptor(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        u_descriptor = self._arrays.get(array_hash)
        if u_descriptor is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if u_descriptor.ctypes.data != array_handle:
                u_descriptor = None
        if u_descriptor is None:
            try:
                u_descriptor = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_physio_datadt__array__u_descriptor)
            except TypeError:
                u_descriptor = f90wrap.runtime.direct_c_array(array_type, array_shape, \
                    array_handle)
            self._arrays[array_hash] = u_descriptor
        return u_descriptor
    
    @u_descriptor.setter
    def u_descriptor(self, u_descriptor):
        self.u_descriptor[...] = u_descriptor
    
    
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
        "mwd_physio_data".')

for func in _dt_array_initialisers:
    func()
