"""
(MWD) Module Wrapped and Differentiated

Subroutine
----------

- binary_search
- compute_rowcol_to_ind_ac
- matrix_to_ac_vector
- ac_vector_to_matrix
- get_matrix_nnz
- coo_fill_sparse_matrix
- ac_fill_sparse_matrix
- fill_sparse_matrix
- matrix_to_sparse_matrix
- coo_sparse_matrix_to_matrix
- ac_sparse_matrix_to_matrix
- sparse_matrix_to_matrix
- coo_get_sparse_matrix_dat
- ac_get_sparse_matrix_dat
- get_sparse_matrix_dat

Module mwd_sparse_matrix_manipulation
Defined at ../smash/fcore/routine/mwd_sparse_matrix_manipulation.f90 lines \
    21-233
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

def binary_search(n, vector, vle, ind, interface_call=False):
    """
    binary_search(n, vector, vle, ind)
    Defined at ../smash/fcore/routine/mwd_sparse_matrix_manipulation.f90 lines 29-49
    
    Parameters
    ----------
    n : int32
    vector : int array
    vle : int32
    ind : int32
    """
    _libfcore.f90wrap_mwd_sparse_matrix_manipulation__binary_search(n=n, \
        vector=vector, vle=vle, ind=ind)

def compute_rowcol_to_ind_ac(self, interface_call=False):
    """
    Notes
    -----
    
    compute_rowcol_to_ind_ac(self)
    Defined at ../smash/fcore/routine/mwd_sparse_matrix_manipulation.f90 lines 51-64
    
    Parameters
    ----------
    mesh : Meshdt
    """
    _libfcore.f90wrap_mwd_sparse_matrix_manipulation__compute_rowcol_to_i2d41(mesh=self._handle)

def matrix_to_ac_vector(self, matrix, ac_vector, interface_call=False):
    """
    matrix_to_ac_vector(self, matrix, ac_vector)
    Defined at ../smash/fcore/routine/mwd_sparse_matrix_manipulation.f90 lines 66-78
    
    Parameters
    ----------
    mesh : Meshdt
    matrix : float array
    ac_vector : float array
    """
    _libfcore.f90wrap_mwd_sparse_matrix_manipulation__matrix_to_ac_vector(mesh=self._handle, \
        matrix=matrix, ac_vector=ac_vector)

def ac_vector_to_matrix(self, ac_vector, matrix, interface_call=False):
    """
    ac_vector_to_matrix(self, ac_vector, matrix)
    Defined at ../smash/fcore/routine/mwd_sparse_matrix_manipulation.f90 lines 80-92
    
    Parameters
    ----------
    mesh : Meshdt
    ac_vector : float array
    matrix : float array
    """
    _libfcore.f90wrap_mwd_sparse_matrix_manipulation__ac_vector_to_matrix(mesh=self._handle, \
        ac_vector=ac_vector, matrix=matrix)

def get_matrix_nnz(self, matrix, zvalue, nnz, interface_call=False):
    """
    get_matrix_nnz(self, matrix, zvalue, nnz)
    Defined at ../smash/fcore/routine/mwd_sparse_matrix_manipulation.f90 lines \
        94-107
    
    Parameters
    ----------
    mesh : Meshdt
    matrix : float array
    zvalue : float32
    nnz : int32
    """
    _libfcore.f90wrap_mwd_sparse_matrix_manipulation__get_matrix_nnz(mesh=self._handle, \
        matrix=matrix, zvalue=zvalue, nnz=nnz)

def coo_fill_sparse_matrix(self, matrix, sparse_matrix, interface_call=False):
    """
    coo_fill_sparse_matrix(self, matrix, sparse_matrix)
    Defined at ../smash/fcore/routine/mwd_sparse_matrix_manipulation.f90 lines \
        109-123
    
    Parameters
    ----------
    mesh : Meshdt
    matrix : float array
    sparse_matrix : Sparse_Matrixdt
    """
    _libfcore.f90wrap_mwd_sparse_matrix_manipulation__coo_fill_sparse_matrix(mesh=self._handle, \
        matrix=matrix, sparse_matrix=sparse_matrix._handle)

def ac_fill_sparse_matrix(self, matrix, sparse_matrix, interface_call=False):
    """
    ac_fill_sparse_matrix(self, matrix, sparse_matrix)
    Defined at ../smash/fcore/routine/mwd_sparse_matrix_manipulation.f90 lines \
        125-129
    
    Parameters
    ----------
    mesh : Meshdt
    matrix : float array
    sparse_matrix : Sparse_Matrixdt
    """
    _libfcore.f90wrap_mwd_sparse_matrix_manipulation__ac_fill_sparse_matrix(mesh=self._handle, \
        matrix=matrix, sparse_matrix=sparse_matrix._handle)

def fill_sparse_matrix(self, matrix, sparse_matrix, interface_call=False):
    """
    fill_sparse_matrix(self, matrix, sparse_matrix)
    Defined at ../smash/fcore/routine/mwd_sparse_matrix_manipulation.f90 lines \
        131-139
    
    Parameters
    ----------
    mesh : Meshdt
    matrix : float array
    sparse_matrix : Sparse_Matrixdt
    """
    _libfcore.f90wrap_mwd_sparse_matrix_manipulation__fill_sparse_matrix(mesh=self._handle, \
        matrix=matrix, sparse_matrix=sparse_matrix._handle)

def matrix_to_sparse_matrix(self, matrix, zvalue, sparse_matrix, \
    interface_call=False):
    """
    Do not need to cast to real
    
    matrix_to_sparse_matrix(self, matrix, zvalue, sparse_matrix)
    Defined at ../smash/fcore/routine/mwd_sparse_matrix_manipulation.f90 lines \
        141-159
    
    Parameters
    ----------
    mesh : Meshdt
    matrix : float array
    zvalue : float32
    sparse_matrix : Sparse_Matrixdt
    """
    _libfcore.f90wrap_mwd_sparse_matrix_manipulation__matrix_to_sparse_matrix(mesh=self._handle, \
        matrix=matrix, zvalue=zvalue, sparse_matrix=sparse_matrix._handle)

def coo_sparse_matrix_to_matrix(self, sparse_matrix, matrix, \
    interface_call=False):
    """
    coo_sparse_matrix_to_matrix(self, sparse_matrix, matrix)
    Defined at ../smash/fcore/routine/mwd_sparse_matrix_manipulation.f90 lines \
        161-178
    
    Parameters
    ----------
    mesh : Meshdt
    sparse_matrix : Sparse_Matrixdt
    matrix : float array
    """
    _libfcore.f90wrap_mwd_sparse_matrix_manipulation__coo_sparse_matrix_t64d3(mesh=self._handle, \
        sparse_matrix=sparse_matrix._handle, matrix=matrix)

def ac_sparse_matrix_to_matrix(self, sparse_matrix, matrix, \
    interface_call=False):
    """
    ac_sparse_matrix_to_matrix(self, sparse_matrix, matrix)
    Defined at ../smash/fcore/routine/mwd_sparse_matrix_manipulation.f90 lines \
        180-185
    
    Parameters
    ----------
    mesh : Meshdt
    sparse_matrix : Sparse_Matrixdt
    matrix : float array
    """
    _libfcore.f90wrap_mwd_sparse_matrix_manipulation__ac_sparse_matrix_to401c(mesh=self._handle, \
        sparse_matrix=sparse_matrix._handle, matrix=matrix)

def sparse_matrix_to_matrix(self, sparse_matrix, matrix, interface_call=False):
    """
    sparse_matrix_to_matrix(self, sparse_matrix, matrix)
    Defined at ../smash/fcore/routine/mwd_sparse_matrix_manipulation.f90 lines \
        187-198
    
    Parameters
    ----------
    mesh : Meshdt
    sparse_matrix : Sparse_Matrixdt
    matrix : float array
    """
    _libfcore.f90wrap_mwd_sparse_matrix_manipulation__sparse_matrix_to_matrix(mesh=self._handle, \
        sparse_matrix=sparse_matrix._handle, matrix=matrix)

def coo_get_sparse_matrix_dat(self, row, col, sparse_matrix, res, \
    interface_call=False):
    """
    coo_get_sparse_matrix_dat(self, row, col, sparse_matrix, res)
    Defined at ../smash/fcore/routine/mwd_sparse_matrix_manipulation.f90 lines \
        200-209
    
    Parameters
    ----------
    mesh : Meshdt
    row : int32
    col : int32
    sparse_matrix : Sparse_Matrixdt
    res : float32
    """
    _libfcore.f90wrap_mwd_sparse_matrix_manipulation__coo_get_sparse_matre4b5(mesh=self._handle, \
        row=row, col=col, sparse_matrix=sparse_matrix._handle, res=res)

def ac_get_sparse_matrix_dat(self, row, col, sparse_matrix, res, \
    interface_call=False):
    """
    ac_get_sparse_matrix_dat(self, row, col, sparse_matrix, res)
    Defined at ../smash/fcore/routine/mwd_sparse_matrix_manipulation.f90 lines \
        211-219
    
    Parameters
    ----------
    mesh : Meshdt
    row : int32
    col : int32
    sparse_matrix : Sparse_Matrixdt
    res : float32
    """
    _libfcore.f90wrap_mwd_sparse_matrix_manipulation__ac_get_sparse_matri0419(mesh=self._handle, \
        row=row, col=col, sparse_matrix=sparse_matrix._handle, res=res)

def get_sparse_matrix_dat(self, row, col, sparse_matrix, res, \
    interface_call=False):
    """
    get_sparse_matrix_dat(self, row, col, sparse_matrix, res)
    Defined at ../smash/fcore/routine/mwd_sparse_matrix_manipulation.f90 lines \
        221-233
    
    Parameters
    ----------
    mesh : Meshdt
    row : int32
    col : int32
    sparse_matrix : Sparse_Matrixdt
    res : float32
    """
    _libfcore.f90wrap_mwd_sparse_matrix_manipulation__get_sparse_matrix_dat(mesh=self._handle, \
        row=row, col=col, sparse_matrix=sparse_matrix._handle, res=res)


_array_initialisers = []
_dt_array_initialisers = []

try:
    for func in _array_initialisers:
        func()
except ValueError:
    logger.debug('unallocated array(s) detected on import of module \
        "mwd_sparse_matrix_manipulation".')

for func in _dt_array_initialisers:
    func()
