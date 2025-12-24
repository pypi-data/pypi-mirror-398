"""
(MWD) Module Wrapped and Differentiated.

Type
----

- Common_OptionsDT
Common options passed by user

======================== =======================================
`Variables`              Description
======================== =======================================
``ncpu``                 Number of CPUs(default: 1)
``verbose``              Enable verbose(default: .true.)
======================== =======================================

Subroutine
----------

- Common_OptionsDT_initialise
- Common_OptionsDT_copy

Module mwd_common_options
Defined at ../smash/fcore/derived_type/mwd_common_options.f90 lines 21-36
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

@f90wrap.runtime.register_class("libfcore.Common_OptionsDT")
class Common_OptionsDT(f90wrap.runtime.FortranDerivedType):
    """
    Type(name=common_optionsdt)
    Defined at ../smash/fcore/derived_type/mwd_common_options.f90 lines 23-25
    """
    def __init__(self, handle=None):
        """
        self = Common_Optionsdt()
        Defined at ../smash/fcore/derived_type/mwd_common_options.f90 lines 28-30
        
        Returns
        -------
        this : Common_Optionsdt
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num \
            == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = _libfcore.f90wrap_mwd_common_options__common_optionsdt_initialise()
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(_libfcore, \
                "f90wrap_mwd_common_options__common_optionsdt_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    def copy(self, interface_call=False):
        """
        this_copy = common_optionsdt_copy(self)
        Defined at ../smash/fcore/derived_type/mwd_common_options.f90 lines 32-36
        
        Parameters
        ----------
        this : Common_Optionsdt
        
        Returns
        -------
        this_copy : Common_Optionsdt
        """
        this_copy = \
            _libfcore.f90wrap_mwd_common_options__common_optionsdt_copy(this=self._handle)
        this_copy = \
            f90wrap.runtime.lookup_class("libfcore.Common_OptionsDT").from_handle(this_copy, \
            alloc=True)
        this_copy._setup_finalizer()
        return this_copy
    
    @property
    def ncpu(self):
        """
        Element ncpu ftype=integer  pytype=int32
        Defined at ../smash/fcore/derived_type/mwd_common_options.f90 line 24
        """
        return _libfcore.f90wrap_common_optionsdt__get__ncpu(self._handle)
    
    @ncpu.setter
    def ncpu(self, ncpu):
        _libfcore.f90wrap_common_optionsdt__set__ncpu(self._handle, ncpu)
    
    @property
    def verbose(self):
        """
        Element verbose ftype=logical pytype=bool
        Defined at ../smash/fcore/derived_type/mwd_common_options.f90 line 25
        """
        return _libfcore.f90wrap_common_optionsdt__get__verbose(self._handle)
    
    @verbose.setter
    def verbose(self, verbose):
        _libfcore.f90wrap_common_optionsdt__set__verbose(self._handle, verbose)
    
    
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
        "mwd_common_options".')

for func in _dt_array_initialisers:
    func()
