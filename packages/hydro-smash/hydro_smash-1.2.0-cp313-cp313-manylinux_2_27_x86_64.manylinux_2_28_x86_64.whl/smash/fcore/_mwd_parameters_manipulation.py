"""
(MWD) Module Wrapped and Differentiated

Subroutine
----------

- get_serr_mu
- get_serr_sigma
- get_rr_parameters
- get_rr_states
- get_serr_mu_parameters
- get_serr_sigma_parameters
- set_rr_parameters
- set_rr_states
- set_serr_mu_parameters
- set_serr_sigma_parameters
- sigmoide
- inv_sigmoide
- scaled_sigmoide
- inv_scaled_sigmoid
- sigmoide2d
- scaled_sigmoide2d
- sbs_control_tfm
- sbs_inv_control_tfm
- normalize_control_tfm
- normalize_inv_control_tfm
- control_tfm
- inv_control_tfm
- uniform_rr_parameters_get_control_size
- uniform_rr_initial_states_get_control_size
- distributed_rr_parameters_get_control_size
- distributed_rr_initial_states_get_control_size
- multi_linear_rr_parameters_get_control_size
- multi_linear_rr_initial_states_get_control_size
- multi_power_rr_parameters_get_control_size
- multi_power_rr_initial_states_get_control_size
- serr_mu_parameters_get_control_size
- nn_parameters_get_control_size
- get_control_sizes
- uniform_rr_parameters_fill_control
- uniform_rr_initial_states_fill_control
- distributed_rr_parameters_fill_control
- distributed_rr_initial_states_fill_control
- multi_linear_rr_parameters_fill_control
- multi_linear_rr_initial_states_fill_control
- multi_power_rr_parameters_fill_control
- multi_power_rr_initial_states_fill_control
- serr_mu_parameters_fill_control
- serr_sigma_parameters_fill_control
- nn_parameters_fill_control
- fill_control
- uniform_rr_parameters_fill_parameters
- uniform_rr_initial_states_fill_parameters
- distributed_rr_parameters_fill_parameters
- distributed_rr_initial_states_fill_parameters
- multi_linear_rr_parameters_fill_parameters
- multi_linear_rr_initial_states_fill_parameters
- multi_power_rr_parameters_fill_parameters
- multi_power_rr_initial_states_fill_parameters
- serr_mu_parameters_fill_parameters
- serr_sigma_parameters_fill_parameters
- nn_parameters_fill_parameters
- fill_parameters

Module mwd_parameters_manipulation
Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 63-1201
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

def get_serr_mu(self, mesh, parameters, output, serr_mu, interface_call=False):
    """
    only: MuFunk_vect, SigmaFunk_vect
    only: sp, dp
    only: SetupDT
    only: MeshDT
    only: Input_DataDT
    only: ParametersDT
    only: RR_ParametersDT
    only: RR_StatesDT
    only: SErr_Mu_ParametersDT
    only: SErr_Sigma_ParametersDT
    only: OutputDT
    only: OptionsDT
    only: ReturnsDT
    only: ControlDT_initialise, ControlDT_finalise
    
    get_serr_mu(self, mesh, parameters, output, serr_mu)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 81-95
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    parameters : Parametersdt
    output : Outputdt
    serr_mu : float array
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__get_serr_mu(setup=self._handle, \
        mesh=mesh._handle, parameters=parameters._handle, output=output._handle, \
        serr_mu=serr_mu)

def get_serr_sigma(self, mesh, parameters, output, serr_sigma, \
    interface_call=False):
    """
    get_serr_sigma(self, mesh, parameters, output, serr_sigma)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 99-113
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    parameters : Parametersdt
    output : Outputdt
    serr_sigma : float array
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__get_serr_sigma(setup=self._handle, \
        mesh=mesh._handle, parameters=parameters._handle, output=output._handle, \
        serr_sigma=serr_sigma)

def get_rr_parameters(self, key, vle, interface_call=False):
    """
    get_rr_parameters(self, key, vle)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 116-129
    
    Parameters
    ----------
    rr_parameters : Rr_Parametersdt
    key : str
    vle : float array
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__get_rr_parameters(rr_parameters=self._handle, \
        key=key, vle=vle)

def get_rr_states(self, key, vle, interface_call=False):
    """
    get_rr_states(self, key, vle)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 131-144
    
    Parameters
    ----------
    rr_states : Rr_Statesdt
    key : str
    vle : float array
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__get_rr_states(rr_states=self._handle, \
        key=key, vle=vle)

def get_serr_mu_parameters(self, key, vle, interface_call=False):
    """
    get_serr_mu_parameters(self, key, vle)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 146-159
    
    Parameters
    ----------
    serr_mu_parameters : Serr_Mu_Parametersdt
    key : str
    vle : float array
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__get_serr_mu_parameters(serr_mu_parameters=self._handle, \
        key=key, vle=vle)

def get_serr_sigma_parameters(self, key, vle, interface_call=False):
    """
    get_serr_sigma_parameters(self, key, vle)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 161-174
    
    Parameters
    ----------
    serr_sigma_parameters : Serr_Sigma_Parametersdt
    key : str
    vle : float array
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__get_serr_sigma_parameters(serr_sigma_parameters=self._handle, \
        key=key, vle=vle)

def set_rr_parameters(self, key, vle, interface_call=False):
    """
    set_rr_parameters(self, key, vle)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 176-189
    
    Parameters
    ----------
    rr_parameters : Rr_Parametersdt
    key : str
    vle : float array
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__set_rr_parameters(rr_parameters=self._handle, \
        key=key, vle=vle)

def set_rr_states(self, key, vle, interface_call=False):
    """
    set_rr_states(self, key, vle)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 191-204
    
    Parameters
    ----------
    rr_states : Rr_Statesdt
    key : str
    vle : float array
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__set_rr_states(rr_states=self._handle, \
        key=key, vle=vle)

def set_serr_mu_parameters(self, key, vle, interface_call=False):
    """
    set_serr_mu_parameters(self, key, vle)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 206-219
    
    Parameters
    ----------
    serr_mu_parameters : Serr_Mu_Parametersdt
    key : str
    vle : float array
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__set_serr_mu_parameters(serr_mu_parameters=self._handle, \
        key=key, vle=vle)

def set_serr_sigma_parameters(self, key, vle, interface_call=False):
    """
    set_serr_sigma_parameters(self, key, vle)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 221-234
    
    Parameters
    ----------
    serr_sigma_parameters : Serr_Sigma_Parametersdt
    key : str
    vle : float array
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__set_serr_sigma_parameters(serr_sigma_parameters=self._handle, \
        key=key, vle=vle)

def sigmoide(x, res, interface_call=False):
    """
    sigmoide(x, res)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 236-240
    
    Parameters
    ----------
    x : float32
    res : float32
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__sigmoide(x=x, res=res)

def inv_sigmoide(x, res, interface_call=False):
    """
    inv_sigmoide(x, res)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 242-246
    
    Parameters
    ----------
    x : float32
    res : float32
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__inv_sigmoide(x=x, res=res)

def scaled_sigmoide(x, l, u, res, interface_call=False):
    """
    scaled_sigmoide(x, l, u, res)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 248-253
    
    Parameters
    ----------
    x : float32
    l : float32
    u : float32
    res : float32
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__scaled_sigmoide(x=x, l=l, u=u, \
        res=res)

def inv_scaled_sigmoid(x, l, u, res, interface_call=False):
    """
    inv_scaled_sigmoid(x, l, u, res)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 255-263
    
    Parameters
    ----------
    x : float32
    l : float32
    u : float32
    res : float32
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__inv_scaled_sigmoid(x=x, l=l, u=u, \
        res=res)

def sigmoide2d(x, res, interface_call=False):
    """
    sigmoide2d(x, res)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 265-269
    
    Parameters
    ----------
    x : float array
    res : float array
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__sigmoide2d(x=x, res=res)

def scaled_sigmoide2d(x, l, u, res, interface_call=False):
    """
    scaled_sigmoide2d(x, l, u, res)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 271-277
    
    Parameters
    ----------
    x : float array
    l : float32
    u : float32
    res : float array
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__scaled_sigmoide2d(x=x, l=l, u=u, \
        res=res)

def sbs_control_tfm(self, interface_call=False):
    """
    sbs_control_tfm(self)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 279-302
    
    Parameters
    ----------
    parameters : Parametersdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__sbs_control_tfm(parameters=self._handle)

def sbs_inv_control_tfm(self, interface_call=False):
    """
    sbs_inv_control_tfm(self)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 304-323
    
    Parameters
    ----------
    parameters : Parametersdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__sbs_inv_control_tfm(parameters=self._handle)

def normalize_control_tfm(self, interface_call=False):
    """
    normalize_control_tfm(self)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 325-336
    
    Parameters
    ----------
    parameters : Parametersdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__normalize_control_tfm(parameters=self._handle)

def normalize_inv_control_tfm(self, interface_call=False):
    """
    normalize_inv_control_tfm(self)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 338-349
    
    Parameters
    ----------
    parameters : Parametersdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__normalize_inv_control_tfm(parameters=self._handle)

def control_tfm(self, options, interface_call=False):
    """
    control_tfm(self, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 351-360
    
    Parameters
    ----------
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__control_tfm(parameters=self._handle, \
        options=options._handle)

def inv_control_tfm(self, options, interface_call=False):
    """
    inv_control_tfm(self, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 362-371
    
    Parameters
    ----------
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__inv_control_tfm(parameters=self._handle, \
        options=options._handle)

def uniform_rr_parameters_get_control_size(self, n, interface_call=False):
    """
    uniform_rr_parameters_get_control_size(self, n)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 373-377
    
    Parameters
    ----------
    options : Optionsdt
    n : int32
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__uniform_rr_parameters_0c05(options=self._handle, \
        n=n)

def uniform_rr_initial_states_get_control_size(self, n, interface_call=False):
    """
    uniform_rr_initial_states_get_control_size(self, n)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 379-383
    
    Parameters
    ----------
    options : Optionsdt
    n : int32
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__uniform_rr_initial_stac953(options=self._handle, \
        n=n)

def distributed_rr_parameters_get_control_size(self, options, n, \
    interface_call=False):
    """
    distributed_rr_parameters_get_control_size(self, options, n)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 385-390
    
    Parameters
    ----------
    mesh : Meshdt
    options : Optionsdt
    n : int32
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__distributed_rr_parametcae7(mesh=self._handle, \
        options=options._handle, n=n)

def distributed_rr_initial_states_get_control_size(self, options, n, \
    interface_call=False):
    """
    distributed_rr_initial_states_get_control_size(self, options, n)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 392-397
    
    Parameters
    ----------
    mesh : Meshdt
    options : Optionsdt
    n : int32
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__distributed_rr_initial6c7f(mesh=self._handle, \
        options=options._handle, n=n)

def multi_linear_rr_parameters_get_control_size(self, options, n, \
    interface_call=False):
    """
    multi_linear_rr_parameters_get_control_size(self, options, n)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 399-409
    
    Parameters
    ----------
    setup : Setupdt
    options : Optionsdt
    n : int32
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__multi_linear_rr_parameb107(setup=self._handle, \
        options=options._handle, n=n)

def multi_linear_rr_initial_states_get_control_size(self, options, n, \
    interface_call=False):
    """
    multi_linear_rr_initial_states_get_control_size(self, options, n)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 411-421
    
    Parameters
    ----------
    setup : Setupdt
    options : Optionsdt
    n : int32
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__multi_linear_rr_initia6aa2(setup=self._handle, \
        options=options._handle, n=n)

def multi_power_rr_parameters_get_control_size(self, options, n, \
    interface_call=False):
    """
    multi_power_rr_parameters_get_control_size(self, options, n)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 423-433
    
    Parameters
    ----------
    setup : Setupdt
    options : Optionsdt
    n : int32
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__multi_power_rr_parametba5f(setup=self._handle, \
        options=options._handle, n=n)

def multi_power_rr_initial_states_get_control_size(self, options, n, \
    interface_call=False):
    """
    multi_power_rr_initial_states_get_control_size(self, options, n)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 435-445
    
    Parameters
    ----------
    setup : Setupdt
    options : Optionsdt
    n : int32
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__multi_power_rr_initial6761(setup=self._handle, \
        options=options._handle, n=n)

def serr_mu_parameters_get_control_size(self, n, interface_call=False):
    """
    serr_mu_parameters_get_control_size(self, n)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 447-451
    
    Parameters
    ----------
    options : Optionsdt
    n : int32
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__serr_mu_parameters_geta548(options=self._handle, \
        n=n)

def serr_sigma_parameters_get_control_size(self, n, interface_call=False):
    """
    serr_sigma_parameters_get_control_size(self, n)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 453-457
    
    Parameters
    ----------
    options : Optionsdt
    n : int32
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__serr_sigma_parameters_91dd(options=self._handle, \
        n=n)

def nn_parameters_get_control_size(self, options, n, interface_call=False):
    """
    nn_parameters_get_control_size(self, options, n)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 459-470
    
    Parameters
    ----------
    setup : Setupdt
    options : Optionsdt
    n : int32
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__nn_parameters_get_contd3ef(setup=self._handle, \
        options=options._handle, n=n)

def get_control_sizes(self, mesh, options, nbk, interface_call=False):
    """
    get_control_sizes(self, mesh, options, nbk)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 472-498
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    options : Optionsdt
    nbk : int array
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__get_control_sizes(setup=self._handle, \
        mesh=mesh._handle, options=options._handle, nbk=nbk)

def uniform_rr_parameters_fill_control(self, mesh, parameters, options, \
    interface_call=False):
    """
    uniform_rr_parameters_fill_control(self, mesh, parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 500-519
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__uniform_rr_parameters_92c8(setup=self._handle, \
        mesh=mesh._handle, parameters=parameters._handle, options=options._handle)

def uniform_rr_initial_states_fill_control(self, mesh, parameters, options, \
    interface_call=False):
    """
    uniform_rr_initial_states_fill_control(self, mesh, parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 521-540
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__uniform_rr_initial_staa8e6(setup=self._handle, \
        mesh=mesh._handle, parameters=parameters._handle, options=options._handle)

def distributed_rr_parameters_fill_control(self, mesh, parameters, options, \
    interface_call=False):
    """
    distributed_rr_parameters_fill_control(self, mesh, parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 542-566
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__distributed_rr_parameta7ce(setup=self._handle, \
        mesh=mesh._handle, parameters=parameters._handle, options=options._handle)

def distributed_rr_initial_states_fill_control(self, mesh, parameters, options, \
    interface_call=False):
    """
    distributed_rr_initial_states_fill_control(self, mesh, parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 568-592
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__distributed_rr_initial8cf9(setup=self._handle, \
        mesh=mesh._handle, parameters=parameters._handle, options=options._handle)

def multi_linear_rr_parameters_fill_control(self, mesh, parameters, options, \
    interface_call=False):
    """
    multi_linear_rr_parameters_fill_control(self, mesh, parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 594-623
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__multi_linear_rr_parame3564(setup=self._handle, \
        mesh=mesh._handle, parameters=parameters._handle, options=options._handle)

def multi_linear_rr_initial_states_fill_control(self, mesh, parameters, options, \
    interface_call=False):
    """
    multi_linear_rr_initial_states_fill_control(self, mesh, parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 625-654
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__multi_linear_rr_initia6937(setup=self._handle, \
        mesh=mesh._handle, parameters=parameters._handle, options=options._handle)

def multi_power_rr_parameters_fill_control(self, mesh, parameters, options, \
    interface_call=False):
    """
    multi_power_rr_parameters_fill_control(self, mesh, parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 656-691
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__multi_power_rr_paramet6378(setup=self._handle, \
        mesh=mesh._handle, parameters=parameters._handle, options=options._handle)

def multi_power_rr_initial_states_fill_control(self, mesh, parameters, options, \
    interface_call=False):
    """
    multi_power_rr_initial_states_fill_control(self, mesh, parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 693-728
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__multi_power_rr_initial51a1(setup=self._handle, \
        mesh=mesh._handle, parameters=parameters._handle, options=options._handle)

def serr_mu_parameters_fill_control(self, mesh, parameters, options, \
    interface_call=False):
    """
    serr_mu_parameters_fill_control(self, mesh, parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 730-750
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__serr_mu_parameters_filce86(setup=self._handle, \
        mesh=mesh._handle, parameters=parameters._handle, options=options._handle)

def serr_sigma_parameters_fill_control(self, mesh, parameters, options, \
    interface_call=False):
    """
    serr_sigma_parameters_fill_control(self, mesh, parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 752-772
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__serr_sigma_parameters_fbb3(setup=self._handle, \
        mesh=mesh._handle, parameters=parameters._handle, options=options._handle)

def nn_parameters_fill_control(self, options, parameters, interface_call=False):
    """
    nn_parameters_fill_control(self, options, parameters)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 774-842
    
    Parameters
    ----------
    setup : Setupdt
    options : Optionsdt
    parameters : Parametersdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__nn_parameters_fill_control(setup=self._handle, \
        options=options._handle, parameters=parameters._handle)

def fill_control(self, mesh, input_data, parameters, options, \
    interface_call=False):
    """
    fill_control(self, mesh, input_data, parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 844-872
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__fill_control(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, \
        parameters=parameters._handle, options=options._handle)

def uniform_rr_parameters_fill_parameters(self, mesh, parameters, options, \
    interface_call=False):
    """
    uniform_rr_parameters_fill_parameters(self, mesh, parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 874-891
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__uniform_rr_parameters_9389(setup=self._handle, \
        mesh=mesh._handle, parameters=parameters._handle, options=options._handle)

def uniform_rr_initial_states_fill_parameters(self, mesh, parameters, options, \
    interface_call=False):
    """
    uniform_rr_initial_states_fill_parameters(self, mesh, parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 893-910
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__uniform_rr_initial_sta49b6(setup=self._handle, \
        mesh=mesh._handle, parameters=parameters._handle, options=options._handle)

def distributed_rr_parameters_fill_parameters(self, mesh, parameters, options, \
    interface_call=False):
    """
    distributed_rr_parameters_fill_parameters(self, mesh, parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 912-930
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__distributed_rr_parametdbfd(setup=self._handle, \
        mesh=mesh._handle, parameters=parameters._handle, options=options._handle)

def distributed_rr_initial_states_fill_parameters(self, mesh, parameters, \
    options, interface_call=False):
    """
    distributed_rr_initial_states_fill_parameters(self, mesh, parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 932-950
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__distributed_rr_initialeb7c(setup=self._handle, \
        mesh=mesh._handle, parameters=parameters._handle, options=options._handle)

def multi_linear_rr_parameters_fill_parameters(self, mesh, input_data, \
    parameters, options, interface_call=False):
    """
    multi_linear_rr_parameters_fill_parameters(self, mesh, input_data, parameters, \
        options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 952-978
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__multi_linear_rr_parame217c(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, \
        parameters=parameters._handle, options=options._handle)

def multi_linear_rr_initial_states_fill_parameters(self, mesh, input_data, \
    parameters, options, interface_call=False):
    """
    multi_linear_rr_initial_states_fill_parameters(self, mesh, input_data, \
        parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines 980-1006
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__multi_linear_rr_initiac3d9(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, \
        parameters=parameters._handle, options=options._handle)

def multi_power_rr_parameters_fill_parameters(self, mesh, input_data, \
    parameters, options, interface_call=False):
    """
    multi_power_rr_parameters_fill_parameters(self, mesh, input_data, parameters, \
        options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines \
        1008-1035
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__multi_power_rr_paramet7493(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, \
        parameters=parameters._handle, options=options._handle)

def multi_power_rr_initial_states_fill_parameters(self, mesh, input_data, \
    parameters, options, interface_call=False):
    """
    multi_power_rr_initial_states_fill_parameters(self, mesh, input_data, \
        parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines \
        1037-1064
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__multi_power_rr_initial3f65(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, \
        parameters=parameters._handle, options=options._handle)

def serr_mu_parameters_fill_parameters(self, mesh, parameters, options, \
    interface_call=False):
    """
    serr_mu_parameters_fill_parameters(self, mesh, parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines \
        1066-1082
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__serr_mu_parameters_fil3c9c(setup=self._handle, \
        mesh=mesh._handle, parameters=parameters._handle, options=options._handle)

def serr_sigma_parameters_fill_parameters(self, mesh, parameters, options, \
    interface_call=False):
    """
    serr_sigma_parameters_fill_parameters(self, mesh, parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines \
        1084-1100
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__serr_sigma_parameters_9ee4(setup=self._handle, \
        mesh=mesh._handle, parameters=parameters._handle, options=options._handle)

def nn_parameters_fill_parameters(self, options, parameters, \
    interface_call=False):
    """
    nn_parameters_fill_parameters(self, options, parameters)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines \
        1102-1151
    
    Parameters
    ----------
    setup : Setupdt
    options : Optionsdt
    parameters : Parametersdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__nn_parameters_fill_parc6a0(setup=self._handle, \
        options=options._handle, parameters=parameters._handle)

def fill_parameters(self, mesh, input_data, parameters, options, \
    interface_call=False):
    """
    fill_parameters(self, mesh, input_data, parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines \
        1153-1177
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__fill_parameters(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, \
        parameters=parameters._handle, options=options._handle)

def parameters_to_control(self, mesh, input_data, parameters, options, \
    interface_call=False):
    """
    parameters_to_control(self, mesh, input_data, parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines \
        1179-1190
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__parameters_to_control(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, \
        parameters=parameters._handle, options=options._handle)

def control_to_parameters(self, mesh, input_data, parameters, options, \
    interface_call=False):
    """
    control_to_parameters(self, mesh, input_data, parameters, options)
    Defined at ../smash/fcore/routine/mwd_parameters_manipulation.f90 lines \
        1192-1201
    
    Parameters
    ----------
    setup : Setupdt
    mesh : Meshdt
    input_data : Input_Datadt
    parameters : Parametersdt
    options : Optionsdt
    """
    _libfcore.f90wrap_mwd_parameters_manipulation__control_to_parameters(setup=self._handle, \
        mesh=mesh._handle, input_data=input_data._handle, \
        parameters=parameters._handle, options=options._handle)


_array_initialisers = []
_dt_array_initialisers = []

try:
    for func in _array_initialisers:
        func()
except ValueError:
    logger.debug('unallocated array(s) detected on import of module \
        "mwd_parameters_manipulation".')

for func in _dt_array_initialisers:
    func()
