"""
(MWD) Module Wrapped and Differentiated.

Type
----

- SetupDT
All user setup informations. See default values in _constant.py DEFAULT_SETUP

========================== =====================================
`Variables`                Description
========================== =====================================
``snow_module``            Snow module
``hydrological_module``    Hydrological module
``routing_module``         Routing module
``neurons``                Number of neurons in trainable layers
``serr_mu_mapping``        Mapping for structural error model
``serr_sigma_mapping``     Mapping for structural error model
``dt``                     Solver time step        [s]
``start_time``             Simulation start time   [%Y%m%d%H%M]
``end_time``               Simulation end time     [%Y%m%d%H%M]
``adjust_interception``    Adjust interception reservoir capacity
``compute_mean_atmos``     Compute mean atmospheric data for each gauge
``read_qobs``              Read observed discharge
``qobs_directory``         Observed discharge directory path
``read_prcp``              Read precipitation
``prcp_format``            Precipitation format
``prcp_conversion_factor`` Precipitation conversion factor
``prcp_directory``         Precipiation directory path
``prcp_access``            Precipiation access tree
``read_pet``               Read potential evapotranspiration
``pet_format``             Potential evapotranspiration format
``pet_conversion_factor``  Potential evapotranpisration conversion factor
``pet_directory``          Potential evapotranspiration directory path
``pet_access``             Potential evapotranspiration access tree
``daily_interannual_pet``  Read daily interannual potential evapotranspiration
``read_snow``              Read snow
``snow_format``            Snow format
``snow_conversion_factor`` Snow conversion factor
``snow_directory``         Snow directory path
``snow_access``            Snow access tree
``read_temp``              Read temperatur
``temp_format``            Temperature format
``temp_directory``         Temperature directory path
``temp_access``            Temperature access tree
``prcp_partitioning``      Precipitation partitioning
``sparse_storage``         Forcing sparse storage
``read_descriptor``        Read descriptor map(s)
``descriptor_format``      Descriptor maps format
``descriptor_directory``   Descriptor maps directory
``descriptor_name``        Descriptor maps names
``structure``              Structure combaining all modules
``snow_module_present``    Presence of snow module
``ntime_step``             Number of time steps
``nd``                     Number of descriptor maps
``hidden_neuron``          Number of neurons in hidden layers
``n_layers``               Number of trainable layers
``nrrp``                   Number of rainfall-runoff parameters
``nrrs``                   Number of rainfall-runoff states
``nsep_mu``                Number of structural error parameters for mu
``nsep_sigma``             Number of structural error parameters for sigma
``nqz``                    Size of the temporal buffer for discharge grids
``n_internal_fluxes``      Number of internal fluxes
``n_snow_fluxes``          Number of internal fluxes of snow module
``n_hydro_fluxes``         Number of internal fluxes of hydrological module
``n_routing_fluxes``       Number of internal fluxes of routing module

Subroutine
----------

- SetupDT_initialise
- SetupDT_copy

Module mwd_setup
Defined at ../smash/fcore/derived_type/mwd_setup.f90 lines 72-155
"""
from __future__ import print_function, absolute_import, division
from smash.fcore._f90wrap_decorator import f90wrap_getter_char_array, f90wrap_setter_char_array
from smash.fcore._f90wrap_decorator import f90wrap_getter_char, f90wrap_setter_char
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

@f90wrap.runtime.register_class("libfcore.SetupDT")
class SetupDT(f90wrap.runtime.FortranDerivedType):
    """
    Notes
    -----
    SetupDT Derived Type.User variables
    
    Type(name=setupdt)
    Defined at ../smash/fcore/derived_type/mwd_setup.f90 lines 75-137
    """
    def __init__(self, nd, handle=None):
        """
        Notes
        -----
        SetupDT initialisation subroutine
        only: sp, lchar
        
        self = Setupdt(nd)
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 lines 140-149
        
        Parameters
        ----------
        nd : int32
        
        Returns
        -------
        this : Setupdt
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num \
            == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = _libfcore.f90wrap_mwd_setup__setupdt_initialise(nd=nd)
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(_libfcore, "f90wrap_mwd_setup__setupdt_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    def copy(self, interface_call=False):
        """
        this_copy = setupdt_copy(self)
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 lines 151-155
        
        Parameters
        ----------
        this : Setupdt
        
        Returns
        -------
        this_copy : Setupdt
        """
        this_copy = _libfcore.f90wrap_mwd_setup__setupdt_copy(this=self._handle)
        this_copy = \
            f90wrap.runtime.lookup_class("libfcore.SetupDT").from_handle(this_copy, \
            alloc=True)
        this_copy._setup_finalizer()
        return this_copy
    
    @property
    @f90wrap_getter_char
    def snow_module(self):
        """
        Element snow_module ftype=character(lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 80
        """
        return _libfcore.f90wrap_setupdt__get__snow_module(self._handle)
    
    @snow_module.setter
    @f90wrap_setter_char
    def snow_module(self, snow_module):
        _libfcore.f90wrap_setupdt__set__snow_module(self._handle, snow_module)
    
    @property
    @f90wrap_getter_char
    def hydrological_module(self):
        """
        Element hydrological_module ftype=character(lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 81
        """
        return _libfcore.f90wrap_setupdt__get__hydrological_module(self._handle)
    
    @hydrological_module.setter
    @f90wrap_setter_char
    def hydrological_module(self, hydrological_module):
        _libfcore.f90wrap_setupdt__set__hydrological_module(self._handle, \
            hydrological_module)
    
    @property
    @f90wrap_getter_char
    def routing_module(self):
        """
        Element routing_module ftype=character(lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 82
        """
        return _libfcore.f90wrap_setupdt__get__routing_module(self._handle)
    
    @routing_module.setter
    @f90wrap_setter_char
    def routing_module(self, routing_module):
        _libfcore.f90wrap_setupdt__set__routing_module(self._handle, routing_module)
    
    @property
    @f90wrap_getter_char
    def serr_mu_mapping(self):
        """
        Element serr_mu_mapping ftype=character(lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 83
        """
        return _libfcore.f90wrap_setupdt__get__serr_mu_mapping(self._handle)
    
    @serr_mu_mapping.setter
    @f90wrap_setter_char
    def serr_mu_mapping(self, serr_mu_mapping):
        _libfcore.f90wrap_setupdt__set__serr_mu_mapping(self._handle, serr_mu_mapping)
    
    @property
    @f90wrap_getter_char
    def serr_sigma_mapping(self):
        """
        Element serr_sigma_mapping ftype=character(lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 84
        """
        return _libfcore.f90wrap_setupdt__get__serr_sigma_mapping(self._handle)
    
    @serr_sigma_mapping.setter
    @f90wrap_setter_char
    def serr_sigma_mapping(self, serr_sigma_mapping):
        _libfcore.f90wrap_setupdt__set__serr_sigma_mapping(self._handle, \
            serr_sigma_mapping)
    
    @property
    def dt(self):
        """
        Element dt ftype=real(sp) pytype=float32
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 85
        """
        return _libfcore.f90wrap_setupdt__get__dt(self._handle)
    
    @dt.setter
    def dt(self, dt):
        _libfcore.f90wrap_setupdt__set__dt(self._handle, dt)
    
    @property
    @f90wrap_getter_char
    def start_time(self):
        """
        Element start_time ftype=character(lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 86
        """
        return _libfcore.f90wrap_setupdt__get__start_time(self._handle)
    
    @start_time.setter
    @f90wrap_setter_char
    def start_time(self, start_time):
        _libfcore.f90wrap_setupdt__set__start_time(self._handle, start_time)
    
    @property
    @f90wrap_getter_char
    def end_time(self):
        """
        Element end_time ftype=character(lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 87
        """
        return _libfcore.f90wrap_setupdt__get__end_time(self._handle)
    
    @end_time.setter
    @f90wrap_setter_char
    def end_time(self, end_time):
        _libfcore.f90wrap_setupdt__set__end_time(self._handle, end_time)
    
    @property
    def adjust_interception(self):
        """
        Element adjust_interception ftype=logical pytype=bool
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 88
        """
        return _libfcore.f90wrap_setupdt__get__adjust_interception(self._handle)
    
    @adjust_interception.setter
    def adjust_interception(self, adjust_interception):
        _libfcore.f90wrap_setupdt__set__adjust_interception(self._handle, \
            adjust_interception)
    
    @property
    def compute_mean_atmos(self):
        """
        Element compute_mean_atmos ftype=logical pytype=bool
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 89
        """
        return _libfcore.f90wrap_setupdt__get__compute_mean_atmos(self._handle)
    
    @compute_mean_atmos.setter
    def compute_mean_atmos(self, compute_mean_atmos):
        _libfcore.f90wrap_setupdt__set__compute_mean_atmos(self._handle, \
            compute_mean_atmos)
    
    @property
    def read_qobs(self):
        """
        Element read_qobs ftype=logical pytype=bool
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 90
        """
        return _libfcore.f90wrap_setupdt__get__read_qobs(self._handle)
    
    @read_qobs.setter
    def read_qobs(self, read_qobs):
        _libfcore.f90wrap_setupdt__set__read_qobs(self._handle, read_qobs)
    
    @property
    @f90wrap_getter_char
    def qobs_directory(self):
        """
        Element qobs_directory ftype=character(2*lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 91
        """
        return _libfcore.f90wrap_setupdt__get__qobs_directory(self._handle)
    
    @qobs_directory.setter
    @f90wrap_setter_char
    def qobs_directory(self, qobs_directory):
        _libfcore.f90wrap_setupdt__set__qobs_directory(self._handle, qobs_directory)
    
    @property
    def read_prcp(self):
        """
        Element read_prcp ftype=logical pytype=bool
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 92
        """
        return _libfcore.f90wrap_setupdt__get__read_prcp(self._handle)
    
    @read_prcp.setter
    def read_prcp(self, read_prcp):
        _libfcore.f90wrap_setupdt__set__read_prcp(self._handle, read_prcp)
    
    @property
    @f90wrap_getter_char
    def prcp_format(self):
        """
        Element prcp_format ftype=character(lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 93
        """
        return _libfcore.f90wrap_setupdt__get__prcp_format(self._handle)
    
    @prcp_format.setter
    @f90wrap_setter_char
    def prcp_format(self, prcp_format):
        _libfcore.f90wrap_setupdt__set__prcp_format(self._handle, prcp_format)
    
    @property
    def prcp_conversion_factor(self):
        """
        Element prcp_conversion_factor ftype=real(sp) pytype=float32
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 94
        """
        return _libfcore.f90wrap_setupdt__get__prcp_conversion_factor(self._handle)
    
    @prcp_conversion_factor.setter
    def prcp_conversion_factor(self, prcp_conversion_factor):
        _libfcore.f90wrap_setupdt__set__prcp_conversion_factor(self._handle, \
            prcp_conversion_factor)
    
    @property
    @f90wrap_getter_char
    def prcp_directory(self):
        """
        Element prcp_directory ftype=character(2*lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 95
        """
        return _libfcore.f90wrap_setupdt__get__prcp_directory(self._handle)
    
    @prcp_directory.setter
    @f90wrap_setter_char
    def prcp_directory(self, prcp_directory):
        _libfcore.f90wrap_setupdt__set__prcp_directory(self._handle, prcp_directory)
    
    @property
    @f90wrap_getter_char
    def prcp_access(self):
        """
        Element prcp_access ftype=character(lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 96
        """
        return _libfcore.f90wrap_setupdt__get__prcp_access(self._handle)
    
    @prcp_access.setter
    @f90wrap_setter_char
    def prcp_access(self, prcp_access):
        _libfcore.f90wrap_setupdt__set__prcp_access(self._handle, prcp_access)
    
    @property
    def read_pet(self):
        """
        Element read_pet ftype=logical pytype=bool
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 97
        """
        return _libfcore.f90wrap_setupdt__get__read_pet(self._handle)
    
    @read_pet.setter
    def read_pet(self, read_pet):
        _libfcore.f90wrap_setupdt__set__read_pet(self._handle, read_pet)
    
    @property
    @f90wrap_getter_char
    def pet_format(self):
        """
        Element pet_format ftype=character(lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 98
        """
        return _libfcore.f90wrap_setupdt__get__pet_format(self._handle)
    
    @pet_format.setter
    @f90wrap_setter_char
    def pet_format(self, pet_format):
        _libfcore.f90wrap_setupdt__set__pet_format(self._handle, pet_format)
    
    @property
    def pet_conversion_factor(self):
        """
        Element pet_conversion_factor ftype=real(sp) pytype=float32
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 99
        """
        return _libfcore.f90wrap_setupdt__get__pet_conversion_factor(self._handle)
    
    @pet_conversion_factor.setter
    def pet_conversion_factor(self, pet_conversion_factor):
        _libfcore.f90wrap_setupdt__set__pet_conversion_factor(self._handle, \
            pet_conversion_factor)
    
    @property
    @f90wrap_getter_char
    def pet_directory(self):
        """
        Element pet_directory ftype=character(2*lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 100
        """
        return _libfcore.f90wrap_setupdt__get__pet_directory(self._handle)
    
    @pet_directory.setter
    @f90wrap_setter_char
    def pet_directory(self, pet_directory):
        _libfcore.f90wrap_setupdt__set__pet_directory(self._handle, pet_directory)
    
    @property
    @f90wrap_getter_char
    def pet_access(self):
        """
        Element pet_access ftype=character(lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 101
        """
        return _libfcore.f90wrap_setupdt__get__pet_access(self._handle)
    
    @pet_access.setter
    @f90wrap_setter_char
    def pet_access(self, pet_access):
        _libfcore.f90wrap_setupdt__set__pet_access(self._handle, pet_access)
    
    @property
    def daily_interannual_pet(self):
        """
        Element daily_interannual_pet ftype=logical pytype=bool
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 102
        """
        return _libfcore.f90wrap_setupdt__get__daily_interannual_pet(self._handle)
    
    @daily_interannual_pet.setter
    def daily_interannual_pet(self, daily_interannual_pet):
        _libfcore.f90wrap_setupdt__set__daily_interannual_pet(self._handle, \
            daily_interannual_pet)
    
    @property
    def read_snow(self):
        """
        Element read_snow ftype=logical pytype=bool
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 103
        """
        return _libfcore.f90wrap_setupdt__get__read_snow(self._handle)
    
    @read_snow.setter
    def read_snow(self, read_snow):
        _libfcore.f90wrap_setupdt__set__read_snow(self._handle, read_snow)
    
    @property
    @f90wrap_getter_char
    def snow_format(self):
        """
        Element snow_format ftype=character(lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 104
        """
        return _libfcore.f90wrap_setupdt__get__snow_format(self._handle)
    
    @snow_format.setter
    @f90wrap_setter_char
    def snow_format(self, snow_format):
        _libfcore.f90wrap_setupdt__set__snow_format(self._handle, snow_format)
    
    @property
    def snow_conversion_factor(self):
        """
        Element snow_conversion_factor ftype=real(sp) pytype=float32
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 105
        """
        return _libfcore.f90wrap_setupdt__get__snow_conversion_factor(self._handle)
    
    @snow_conversion_factor.setter
    def snow_conversion_factor(self, snow_conversion_factor):
        _libfcore.f90wrap_setupdt__set__snow_conversion_factor(self._handle, \
            snow_conversion_factor)
    
    @property
    @f90wrap_getter_char
    def snow_directory(self):
        """
        Element snow_directory ftype=character(2*lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 106
        """
        return _libfcore.f90wrap_setupdt__get__snow_directory(self._handle)
    
    @snow_directory.setter
    @f90wrap_setter_char
    def snow_directory(self, snow_directory):
        _libfcore.f90wrap_setupdt__set__snow_directory(self._handle, snow_directory)
    
    @property
    @f90wrap_getter_char
    def snow_access(self):
        """
        Element snow_access ftype=character(lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 107
        """
        return _libfcore.f90wrap_setupdt__get__snow_access(self._handle)
    
    @snow_access.setter
    @f90wrap_setter_char
    def snow_access(self, snow_access):
        _libfcore.f90wrap_setupdt__set__snow_access(self._handle, snow_access)
    
    @property
    def read_temp(self):
        """
        Element read_temp ftype=logical pytype=bool
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 108
        """
        return _libfcore.f90wrap_setupdt__get__read_temp(self._handle)
    
    @read_temp.setter
    def read_temp(self, read_temp):
        _libfcore.f90wrap_setupdt__set__read_temp(self._handle, read_temp)
    
    @property
    @f90wrap_getter_char
    def temp_format(self):
        """
        Element temp_format ftype=character(lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 109
        """
        return _libfcore.f90wrap_setupdt__get__temp_format(self._handle)
    
    @temp_format.setter
    @f90wrap_setter_char
    def temp_format(self, temp_format):
        _libfcore.f90wrap_setupdt__set__temp_format(self._handle, temp_format)
    
    @property
    @f90wrap_getter_char
    def temp_directory(self):
        """
        Element temp_directory ftype=character(2*lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 110
        """
        return _libfcore.f90wrap_setupdt__get__temp_directory(self._handle)
    
    @temp_directory.setter
    @f90wrap_setter_char
    def temp_directory(self, temp_directory):
        _libfcore.f90wrap_setupdt__set__temp_directory(self._handle, temp_directory)
    
    @property
    @f90wrap_getter_char
    def temp_access(self):
        """
        Element temp_access ftype=character(lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 111
        """
        return _libfcore.f90wrap_setupdt__get__temp_access(self._handle)
    
    @temp_access.setter
    @f90wrap_setter_char
    def temp_access(self, temp_access):
        _libfcore.f90wrap_setupdt__set__temp_access(self._handle, temp_access)
    
    @property
    def prcp_partitioning(self):
        """
        Element prcp_partitioning ftype=logical pytype=bool
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 112
        """
        return _libfcore.f90wrap_setupdt__get__prcp_partitioning(self._handle)
    
    @prcp_partitioning.setter
    def prcp_partitioning(self, prcp_partitioning):
        _libfcore.f90wrap_setupdt__set__prcp_partitioning(self._handle, \
            prcp_partitioning)
    
    @property
    def sparse_storage(self):
        """
        Element sparse_storage ftype=logical pytype=bool
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 113
        """
        return _libfcore.f90wrap_setupdt__get__sparse_storage(self._handle)
    
    @sparse_storage.setter
    def sparse_storage(self, sparse_storage):
        _libfcore.f90wrap_setupdt__set__sparse_storage(self._handle, sparse_storage)
    
    @property
    def read_descriptor(self):
        """
        Element read_descriptor ftype=logical pytype=bool
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 114
        """
        return _libfcore.f90wrap_setupdt__get__read_descriptor(self._handle)
    
    @read_descriptor.setter
    def read_descriptor(self, read_descriptor):
        _libfcore.f90wrap_setupdt__set__read_descriptor(self._handle, read_descriptor)
    
    @property
    @f90wrap_getter_char
    def descriptor_format(self):
        """
        Element descriptor_format ftype=character(lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 115
        """
        return _libfcore.f90wrap_setupdt__get__descriptor_format(self._handle)
    
    @descriptor_format.setter
    @f90wrap_setter_char
    def descriptor_format(self, descriptor_format):
        _libfcore.f90wrap_setupdt__set__descriptor_format(self._handle, \
            descriptor_format)
    
    @property
    @f90wrap_getter_char
    def descriptor_directory(self):
        """
        Element descriptor_directory ftype=character(2*lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 116
        """
        return _libfcore.f90wrap_setupdt__get__descriptor_directory(self._handle)
    
    @descriptor_directory.setter
    @f90wrap_setter_char
    def descriptor_directory(self, descriptor_directory):
        _libfcore.f90wrap_setupdt__set__descriptor_directory(self._handle, \
            descriptor_directory)
    
    @property
    @f90wrap_getter_char_array
    def descriptor_name(self):
        """
        Element descriptor_name ftype=character(lchar) pytype=str array
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 117
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_setupdt__array__descriptor_name(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        descriptor_name = self._arrays.get(array_hash)
        if descriptor_name is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if descriptor_name.ctypes.data != array_handle:
                descriptor_name = None
        if descriptor_name is None:
            try:
                descriptor_name = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_setupdt__array__descriptor_name)
            except TypeError:
                descriptor_name = f90wrap.runtime.direct_c_array(array_type, array_shape, \
                    array_handle)
            self._arrays[array_hash] = descriptor_name
        return descriptor_name
    
    @descriptor_name.setter
    @f90wrap_setter_char_array
    def descriptor_name(self, descriptor_name):
        self.descriptor_name[...] = descriptor_name
    
    @property
    def read_imperviousness(self):
        """
        Element read_imperviousness ftype=logical pytype=bool
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 118
        """
        return _libfcore.f90wrap_setupdt__get__read_imperviousness(self._handle)
    
    @read_imperviousness.setter
    def read_imperviousness(self, read_imperviousness):
        _libfcore.f90wrap_setupdt__set__read_imperviousness(self._handle, \
            read_imperviousness)
    
    @property
    @f90wrap_getter_char
    def imperviousness_format(self):
        """
        Element imperviousness_format ftype=character(lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 119
        """
        return _libfcore.f90wrap_setupdt__get__imperviousness_format(self._handle)
    
    @imperviousness_format.setter
    @f90wrap_setter_char
    def imperviousness_format(self, imperviousness_format):
        _libfcore.f90wrap_setupdt__set__imperviousness_format(self._handle, \
            imperviousness_format)
    
    @property
    @f90wrap_getter_char
    def imperviousness_file(self):
        """
        Element imperviousness_file ftype=character(2*lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 120
        """
        return _libfcore.f90wrap_setupdt__get__imperviousness_file(self._handle)
    
    @imperviousness_file.setter
    @f90wrap_setter_char
    def imperviousness_file(self, imperviousness_file):
        _libfcore.f90wrap_setupdt__set__imperviousness_file(self._handle, \
            imperviousness_file)
    
    @property
    @f90wrap_getter_char
    def structure(self):
        """
        Element structure ftype=character(lchar) pytype=str
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 122
        """
        return _libfcore.f90wrap_setupdt__get__structure(self._handle)
    
    @structure.setter
    @f90wrap_setter_char
    def structure(self, structure):
        _libfcore.f90wrap_setupdt__set__structure(self._handle, structure)
    
    @property
    def snow_module_present(self):
        """
        Element snow_module_present ftype=logical pytype=bool
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 123
        """
        return _libfcore.f90wrap_setupdt__get__snow_module_present(self._handle)
    
    @snow_module_present.setter
    def snow_module_present(self, snow_module_present):
        _libfcore.f90wrap_setupdt__set__snow_module_present(self._handle, \
            snow_module_present)
    
    @property
    def ntime_step(self):
        """
        Element ntime_step ftype=integer  pytype=int32
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 124
        """
        return _libfcore.f90wrap_setupdt__get__ntime_step(self._handle)
    
    @ntime_step.setter
    def ntime_step(self, ntime_step):
        _libfcore.f90wrap_setupdt__set__ntime_step(self._handle, ntime_step)
    
    @property
    def nd(self):
        """
        Element nd ftype=integer  pytype=int32
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 125
        """
        return _libfcore.f90wrap_setupdt__get__nd(self._handle)
    
    @nd.setter
    def nd(self, nd):
        _libfcore.f90wrap_setupdt__set__nd(self._handle, nd)
    
    @property
    def nrrp(self):
        """
        Element nrrp ftype=integer  pytype=int32
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 126
        """
        return _libfcore.f90wrap_setupdt__get__nrrp(self._handle)
    
    @nrrp.setter
    def nrrp(self, nrrp):
        _libfcore.f90wrap_setupdt__set__nrrp(self._handle, nrrp)
    
    @property
    def nrrs(self):
        """
        Element nrrs ftype=integer  pytype=int32
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 127
        """
        return _libfcore.f90wrap_setupdt__get__nrrs(self._handle)
    
    @nrrs.setter
    def nrrs(self, nrrs):
        _libfcore.f90wrap_setupdt__set__nrrs(self._handle, nrrs)
    
    @property
    def nsep_mu(self):
        """
        Element nsep_mu ftype=integer  pytype=int32
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 128
        """
        return _libfcore.f90wrap_setupdt__get__nsep_mu(self._handle)
    
    @nsep_mu.setter
    def nsep_mu(self, nsep_mu):
        _libfcore.f90wrap_setupdt__set__nsep_mu(self._handle, nsep_mu)
    
    @property
    def nsep_sigma(self):
        """
        Element nsep_sigma ftype=integer  pytype=int32
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 129
        """
        return _libfcore.f90wrap_setupdt__get__nsep_sigma(self._handle)
    
    @nsep_sigma.setter
    def nsep_sigma(self, nsep_sigma):
        _libfcore.f90wrap_setupdt__set__nsep_sigma(self._handle, nsep_sigma)
    
    @property
    def nqz(self):
        """
        Element nqz ftype=integer  pytype=int32
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 130
        """
        return _libfcore.f90wrap_setupdt__get__nqz(self._handle)
    
    @nqz.setter
    def nqz(self, nqz):
        _libfcore.f90wrap_setupdt__set__nqz(self._handle, nqz)
    
    @property
    def n_internal_fluxes(self):
        """
        Element n_internal_fluxes ftype=integer  pytype=int32
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 131
        """
        return _libfcore.f90wrap_setupdt__get__n_internal_fluxes(self._handle)
    
    @n_internal_fluxes.setter
    def n_internal_fluxes(self, n_internal_fluxes):
        _libfcore.f90wrap_setupdt__set__n_internal_fluxes(self._handle, \
            n_internal_fluxes)
    
    @property
    def n_snow_fluxes(self):
        """
        Element n_snow_fluxes ftype=integer  pytype=int32
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 132
        """
        return _libfcore.f90wrap_setupdt__get__n_snow_fluxes(self._handle)
    
    @n_snow_fluxes.setter
    def n_snow_fluxes(self, n_snow_fluxes):
        _libfcore.f90wrap_setupdt__set__n_snow_fluxes(self._handle, n_snow_fluxes)
    
    @property
    def n_hydro_fluxes(self):
        """
        Element n_hydro_fluxes ftype=integer  pytype=int32
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 133
        """
        return _libfcore.f90wrap_setupdt__get__n_hydro_fluxes(self._handle)
    
    @n_hydro_fluxes.setter
    def n_hydro_fluxes(self, n_hydro_fluxes):
        _libfcore.f90wrap_setupdt__set__n_hydro_fluxes(self._handle, n_hydro_fluxes)
    
    @property
    def n_routing_fluxes(self):
        """
        Element n_routing_fluxes ftype=integer  pytype=int32
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 134
        """
        return _libfcore.f90wrap_setupdt__get__n_routing_fluxes(self._handle)
    
    @n_routing_fluxes.setter
    def n_routing_fluxes(self, n_routing_fluxes):
        _libfcore.f90wrap_setupdt__set__n_routing_fluxes(self._handle, n_routing_fluxes)
    
    @property
    def n_layers(self):
        """
        Element n_layers ftype=integer  pytype=int32
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 135
        """
        return _libfcore.f90wrap_setupdt__get__n_layers(self._handle)
    
    @n_layers.setter
    def n_layers(self, n_layers):
        _libfcore.f90wrap_setupdt__set__n_layers(self._handle, n_layers)
    
    @property
    def hidden_neuron(self):
        """
        Element hidden_neuron ftype=integer pytype=int array
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 136
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_setupdt__array__hidden_neuron(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        hidden_neuron = self._arrays.get(array_hash)
        if hidden_neuron is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if hidden_neuron.ctypes.data != array_handle:
                hidden_neuron = None
        if hidden_neuron is None:
            try:
                hidden_neuron = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_setupdt__array__hidden_neuron)
            except TypeError:
                hidden_neuron = f90wrap.runtime.direct_c_array(array_type, array_shape, \
                    array_handle)
            self._arrays[array_hash] = hidden_neuron
        return hidden_neuron
    
    @hidden_neuron.setter
    def hidden_neuron(self, hidden_neuron):
        self.hidden_neuron[...] = hidden_neuron
    
    @property
    def neurons(self):
        """
        Element neurons ftype=integer pytype=int array
        Defined at ../smash/fcore/derived_type/mwd_setup.f90 line 137
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_setupdt__array__neurons(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        neurons = self._arrays.get(array_hash)
        if neurons is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if neurons.ctypes.data != array_handle:
                neurons = None
        if neurons is None:
            try:
                neurons = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_setupdt__array__neurons)
            except TypeError:
                neurons = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = neurons
        return neurons
    
    @neurons.setter
    def neurons(self, neurons):
        self.neurons[...] = neurons
    
    
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
    logger.debug('unallocated array(s) detected on import of module "mwd_setup".')

for func in _dt_array_initialisers:
    func()
