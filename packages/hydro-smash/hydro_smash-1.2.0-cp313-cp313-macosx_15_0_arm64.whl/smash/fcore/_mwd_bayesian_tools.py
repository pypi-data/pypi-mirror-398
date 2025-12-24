"""
Module mwd_bayesian_tools
Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 lines 2-590
"""
from __future__ import print_function, absolute_import, division
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

@f90wrap.runtime.register_class("libfcore.PriorType")
class PriorType(f90wrap.runtime.FortranDerivedType):
    """
    Type(name=priortype)
    Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 lines 13-15
    """
    def __init__(self, n, handle=None):
        """
        self = Priortype(n)
        Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 lines 22-25
        
        Parameters
        ----------
        n : int32
        
        Returns
        -------
        this : Priortype
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num \
            == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = _libfcore.f90wrap_mwd_bayesian_tools__priortype_initialise(n=n)
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(_libfcore, \
                "f90wrap_mwd_bayesian_tools__priortype_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    @property
    @f90wrap_getter_char
    def dist(self):
        """
        Element dist ftype=character(250) pytype=str
        Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 line 14
        """
        return _libfcore.f90wrap_priortype__get__dist(self._handle)
    
    @dist.setter
    @f90wrap_setter_char
    def dist(self, dist):
        _libfcore.f90wrap_priortype__set__dist(self._handle, dist)
    
    @property
    def par(self):
        """
        Element par ftype=real(mrk) pytype=float array
        Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 line 15
        """
        array_ndim, array_type, array_shape, array_handle = \
            _libfcore.f90wrap_priortype__array__par(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        par = self._arrays.get(array_hash)
        if par is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if par.ctypes.data != array_handle:
                par = None
        if par is None:
            try:
                par = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        _libfcore.f90wrap_priortype__array__par)
            except TypeError:
                par = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = par
        return par
    
    @par.setter
    def par(self, par):
        self.par[...] = par
    
    
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
    

def compute_loglkh(obs, uobs, sim, mu_funk, mu_gamma, sigma_funk, sigma_gamma, \
    interface_call=False):
    """
    loglkh, feas, isnull = compute_loglkh(obs, uobs, sim, mu_funk, mu_gamma, \
        sigma_funk, sigma_gamma)
    Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 lines 36-77
    
    Parameters
    ----------
    obs : float array
    uobs : float array
    sim : float array
    mu_funk : str
    mu_gamma : float array
    sigma_funk : str
    sigma_gamma : float array
    
    Returns
    -------
    loglkh : float64
    feas : bool
    isnull : bool
    """
    loglkh, feas, isnull = \
        _libfcore.f90wrap_mwd_bayesian_tools__compute_loglkh(obs=obs, uobs=uobs, \
        sim=sim, mu_funk=mu_funk, mu_gamma=mu_gamma, sigma_funk=sigma_funk, \
        sigma_gamma=sigma_gamma)
    return loglkh, feas, isnull

def compute_logh(interface_call=False):
    """
    logh, feas, isnull = compute_logh()
    Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 lines 105-110
    
    Returns
    -------
    logh : float64
    feas : bool
    isnull : bool
    """
    logh, feas, isnull = _libfcore.f90wrap_mwd_bayesian_tools__compute_logh()
    return logh, feas, isnull

def getparnumber(distid, interface_call=False):
    """
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    npar, err, mess = getparnumber(distid)
    Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 lines 158-193
    
    Parameters
    ----------
    distid : str
    
    Returns
    -------
    npar : int64
    err : int64
    mess : str
    """
    npar, err, mess = \
        _libfcore.f90wrap_mwd_bayesian_tools__getparnumber(distid=distid)
    return npar, err, mess

def getparname(distid, name, interface_call=False):
    """
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    err, mess = getparname(distid, name)
    Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 lines 196-253
    
    Parameters
    ----------
    distid : str
    name : str array
    
    Returns
    -------
    err : int64
    mess : str
    """
    err, mess = _libfcore.f90wrap_mwd_bayesian_tools__getparname(distid=distid, \
        name=name)
    return err, mess

def checkparsize(distid, par, interface_call=False):
    """
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    ok, err, mess = checkparsize(distid, par)
    Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 lines 256-290
    
    Parameters
    ----------
    distid : str
    par : float array
    
    Returns
    -------
    ok : bool
    err : int64
    mess : str
    """
    ok, err, mess = \
        _libfcore.f90wrap_mwd_bayesian_tools__checkparsize(distid=distid, par=par)
    return ok, err, mess

def getparfeas(distid, par, interface_call=False):
    """
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    feas, err, mess = getparfeas(distid, par)
    Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 lines 293-339
    
    Parameters
    ----------
    distid : str
    par : float array
    
    Returns
    -------
    feas : bool
    err : int64
    mess : str
    """
    feas, err, mess = \
        _libfcore.f90wrap_mwd_bayesian_tools__getparfeas(distid=distid, par=par)
    return feas, err, mess

def getpdf(distid, x, par, loga, interface_call=False):
    """
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    pdf, feas, isnull, err, mess = getpdf(distid, x, par, loga)
    Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 lines 342-428
    
    Parameters
    ----------
    distid : str
    x : float64
    par : float array
    loga : bool
    
    Returns
    -------
    pdf : float64
    feas : bool
    isnull : bool
    err : int64
    mess : str
    """
    pdf, feas, isnull, err, mess = \
        _libfcore.f90wrap_mwd_bayesian_tools__getpdf(distid=distid, x=x, par=par, \
        loga=loga)
    return pdf, feas, isnull, err, mess

def sigmafunk_apply(funk, par, y, interface_call=False):
    """
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    res, err, mess = sigmafunk_apply(funk, par, y)
    Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 lines 431-475
    
    Parameters
    ----------
    funk : str
    par : float array
    y : float64
    
    Returns
    -------
    res : float64
    err : int64
    mess : str
    """
    res, err, mess = \
        _libfcore.f90wrap_mwd_bayesian_tools__sigmafunk_apply(funk=funk, par=par, \
        y=y)
    return res, err, mess

def mufunk_apply(funk, par, y, interface_call=False):
    """
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    res, err, mess = mufunk_apply(funk, par, y)
    Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 lines 478-518
    
    Parameters
    ----------
    funk : str
    par : float array
    y : float64
    
    Returns
    -------
    res : float64
    err : int64
    mess : str
    """
    res, err, mess = _libfcore.f90wrap_mwd_bayesian_tools__mufunk_apply(funk=funk, \
        par=par, y=y)
    return res, err, mess

def sigmafunk_vect(funk, par, y, res, interface_call=False):
    """
    sigmafunk_vect(funk, par, y, res)
    Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 lines 520-554
    
    Parameters
    ----------
    funk : str
    par : float array
    y : float array
    res : float array
    """
    _libfcore.f90wrap_mwd_bayesian_tools__sigmafunk_vect(funk=funk, par=par, y=y, \
        res=res)

def mufunk_vect(funk, par, y, res, interface_call=False):
    """
    mufunk_vect(funk, par, y, res)
    Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 lines 556-590
    
    Parameters
    ----------
    funk : str
    par : float array
    y : float array
    res : float array
    """
    _libfcore.f90wrap_mwd_bayesian_tools__mufunk_vect(funk=funk, par=par, y=y, \
        res=res)

def get_mrk():
    """
    Element mrk ftype=integer pytype=int32
    Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 line 5
    """
    return _libfcore.f90wrap_mwd_bayesian_tools__get__mrk()

mrk = get_mrk()

def get_mik():
    """
    Element mik ftype=integer pytype=int32
    Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 line 6
    """
    return _libfcore.f90wrap_mwd_bayesian_tools__get__mik()

mik = get_mik()

def get_len_longstr():
    """
    Element len_longstr ftype=integer(mik) pytype=int64
    Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 line 7
    """
    return _libfcore.f90wrap_mwd_bayesian_tools__get__len_longstr()

len_longStr = get_len_longstr()

def get_undefrn():
    """
    Element undefrn ftype=real(mrk) pytype=float64
    Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 line 8
    """
    return _libfcore.f90wrap_mwd_bayesian_tools__get__undefrn()

undefRN = get_undefrn()

def get_undefin():
    """
    Element undefin ftype=integer(mik) pytype=int64
    Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 line 9
    """
    return _libfcore.f90wrap_mwd_bayesian_tools__get__undefin()

undefIN = get_undefin()

def get_mv():
    """
    Element mv ftype=real(mrk) pytype=float64
    Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 line 10
    """
    return _libfcore.f90wrap_mwd_bayesian_tools__get__mv()

mv = get_mv()

def get_pi():
    """
    Element pi ftype=real(mrk) pytype=float64
    Defined at ../smash/fcore/external/mwd_bayesian_tools.f90 line 11
    """
    return _libfcore.f90wrap_mwd_bayesian_tools__get__pi()

pi = get_pi()


_array_initialisers = []
_dt_array_initialisers = []


try:
    for func in _array_initialisers:
        func()
except ValueError:
    logger.debug('unallocated array(s) detected on import of module \
        "mwd_bayesian_tools".')

for func in _dt_array_initialisers:
    func()
