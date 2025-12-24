"""
(MWD) Module Wrapped and Differentiated.

Subroutine
----------

- baseflow_separation

Function
--------

- rc
- rchf
- rclf
- rch2r
- cfp
- eff
- ebf
- epf
- elt

Module mwd_signatures
Defined at ../smash/fcore/signal_analysis/mwd_signatures.f90 lines 20-348
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

def baseflow_separation(streamflow, bt, qft, filter_parameter, passes, \
    interface_call=False):
    """
    Notes
    -----
    
    Baseflow separation routine
    
    Dafult parameters:
    filter_parameter = 0.925, passes = 3
    only: sp
    only: quantile1d_r
    
    baseflow_separation(streamflow, bt, qft, filter_parameter, passes)
    Defined at ../smash/fcore/signal_analysis/mwd_signatures.f90 lines 25-85
    
    Parameters
    ----------
    streamflow : float array
    bt : float array
    qft : float array
    filter_parameter : float32
    passes : int32
    """
    _libfcore.f90wrap_mwd_signatures__baseflow_separation(streamflow=streamflow, \
        bt=bt, qft=qft, filter_parameter=filter_parameter, passes=passes)

def rc(p, q, interface_call=False):
    """
    Notes
    -----
    
    Runoff Cofficient(Crc or Erc)
    Given two single precision array(p, q) of dim(1) and size(n),
    it returns the result of RC computation
    
    res = rc(p, q)
    Defined at ../smash/fcore/signal_analysis/mwd_signatures.f90 lines 87-110
    
    Parameters
    ----------
    p : float array
    q : float array
    
    Returns
    -------
    res : float32
    """
    res = _libfcore.f90wrap_mwd_signatures__rc(p=p, q=q)
    return res

def rchf(p, q, interface_call=False):
    """
    Notes
    -----
    
    Runoff Cofficient on Highflow(Crchf or Erchf)
    Given two single precision array(p, q) of dim(1) and size(n),
    it returns the result of RCHF computation
    
    res = rchf(p, q)
    Defined at ../smash/fcore/signal_analysis/mwd_signatures.f90 lines 112-147
    
    Parameters
    ----------
    p : float array
    q : float array
    
    Returns
    -------
    res : float32
    """
    res = _libfcore.f90wrap_mwd_signatures__rchf(p=p, q=q)
    return res

def rclf(p, q, interface_call=False):
    """
    Notes
    -----
    
    Runoff Cofficient on Lowflow(Crclf or Erclf)
    Given two single precision array(p, q) of dim(1) and size(n),
    it returns the result of RCLF computation
    
    res = rclf(p, q)
    Defined at ../smash/fcore/signal_analysis/mwd_signatures.f90 lines 149-184
    
    Parameters
    ----------
    p : float array
    q : float array
    
    Returns
    -------
    res : float32
    """
    res = _libfcore.f90wrap_mwd_signatures__rclf(p=p, q=q)
    return res

def rch2r(p, q, interface_call=False):
    """
    Notes
    -----
    
    Runoff Cofficient on Highflow and discharge(Crch2r or Erch2r)
    Given two single precision array(p, q) of dim(1) and size(n),
    it returns the result of RCLF computation
    
    res = rch2r(p, q)
    Defined at ../smash/fcore/signal_analysis/mwd_signatures.f90 lines 186-221
    
    Parameters
    ----------
    p : float array
    q : float array
    
    Returns
    -------
    res : float32
    """
    res = _libfcore.f90wrap_mwd_signatures__rch2r(p=p, q=q)
    return res

def cfp(q, quant, interface_call=False):
    """
    Notes
    -----
    
    Flow percentiles(Cfp2, Cfp10, Cfp50, or Cfp90)
    Given one single precision array q of dim(1) and size(n),
    it returns the result of FP computation
    
    res = cfp(q, quant)
    Defined at ../smash/fcore/signal_analysis/mwd_signatures.f90 lines 223-246
    
    Parameters
    ----------
    q : float array
    quant : float32
    
    Returns
    -------
    res : float32
    """
    res = _libfcore.f90wrap_mwd_signatures__cfp(q=q, quant=quant)
    return res

def eff(q, interface_call=False):
    """
    Notes
    -----
    
    Flood flow(Eff)
    Given one single precision array q of dim(1) and size(n),
    it returns the result of FF computation
    
    res = eff(q)
    Defined at ../smash/fcore/signal_analysis/mwd_signatures.f90 lines 248-272
    
    Parameters
    ----------
    q : float array
    
    Returns
    -------
    res : float32
    """
    res = _libfcore.f90wrap_mwd_signatures__eff(q=q)
    return res

def ebf(q, interface_call=False):
    """
    Notes
    -----
    
    Base flow(Ebf)
    Given one single precision array q of dim(1) and size(n),
    it returns the result of BF computation
    
    res = ebf(q)
    Defined at ../smash/fcore/signal_analysis/mwd_signatures.f90 lines 274-298
    
    Parameters
    ----------
    q : float array
    
    Returns
    -------
    res : float32
    """
    res = _libfcore.f90wrap_mwd_signatures__ebf(q=q)
    return res

def epf(q, interface_call=False):
    """
    Notes
    -----
    
    Peak flow(Epf)
    Given one single precision array q of dim(1) and size(n),
    it returns the result of PF computation
    
    res = epf(q)
    Defined at ../smash/fcore/signal_analysis/mwd_signatures.f90 lines 300-316
    
    Parameters
    ----------
    q : float array
    
    Returns
    -------
    res : float32
    """
    res = _libfcore.f90wrap_mwd_signatures__epf(q=q)
    return res

def elt(p, q, interface_call=False):
    """
    Notes
    -----
    
    Lag time(Elt)
    Given two single precision array(p, q) of dim(1) and size(n),
    it returns the result of LT computation
    
    res = elt(p, q)
    Defined at ../smash/fcore/signal_analysis/mwd_signatures.f90 lines 318-348
    
    Parameters
    ----------
    p : float array
    q : float array
    
    Returns
    -------
    res : float32
    """
    res = _libfcore.f90wrap_mwd_signatures__elt(p=p, q=q)
    return res


_array_initialisers = []
_dt_array_initialisers = []

try:
    for func in _array_initialisers:
        func()
except ValueError:
    logger.debug('unallocated array(s) detected on import of module \
        "mwd_signatures".')

for func in _dt_array_initialisers:
    func()
