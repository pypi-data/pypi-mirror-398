
# Python to C++ conversions
from multipers.filtrations cimport *
from libcpp.vector cimport vector
from libcpp cimport bool
cimport numpy as cnp
import numpy as np
from libc.stdint cimport int32_t, int64_t
from cython.operator cimport dereference





###### ------------------- PY TO CPP
#### ---------- 

cdef inline vector[int32_t] _py2p_i32(int32_t[:] filtration) noexcept nogil:
    # TODO: Is there no directer way to convert a T[:] into a vector[T]?
    # A memcpy would be much quicker than a python/cython for loop...
    # With a continuous memory use, we could also pass the pointers as iterators if we have access to it?
    cdef vector[int32_t] f = vector[int32_t](len(filtration))
    for i in range(len(filtration)):
      f[i] = filtration[i]
    return f

cdef inline vector[int32_t] _py2p2_i32(int32_t[:,:] filtrations) noexcept nogil:
    cdef vector[int32_t] f = vector[int32_t](filtrations.shape[0] * filtrations.shape[1])
    k = 0
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[k] = filtrations[i,j]
          k = k + 1
    return f

cdef inline vector[Point[int32_t]] _py2vp_i32(int32_t[:,:] filtrations) noexcept nogil:
    cdef vector[Point[int32_t]] out
    cdef Point[int32_t] f = Point[int32_t](filtrations.shape[1])
    out.reserve(filtrations.shape[0])
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[j] = filtrations[i,j]
        out.emplace_back(f)
    return out

cdef inline Multi_critical_filtration[int32_t] _py2kc_i32(int32_t[:,:] filtrations) noexcept nogil:
    # cdef int32_t[:,:] filtrations = np.asarray(filtrations_, dtype=np.int32)
    cdef vector[int32_t] f = vector[int32_t](filtrations.shape[0] * filtrations.shape[1])
    cdef int k = 0;
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
            f[k] = filtrations[i,j]
            k = k + 1
    cdef Multi_critical_filtration[int32_t] out = Multi_critical_filtration[int32_t](f.begin(), f.end(), filtrations.shape[1])
    out.simplify()
    return out

cdef inline One_critical_filtration[int32_t] _py21c_i32(int32_t[:] filtration) noexcept nogil:
    cdef One_critical_filtration[int32_t] out = _py2p_i32(filtration)
    return out


cdef inline vector[One_critical_filtration[int32_t]] _py2v1c_i32(int32_t[:,:] filtrations) noexcept nogil:
    # cdef int32_t[:,:] filtrations = np.asarray(filtrations_, dtype=np.int32)
    cdef vector[One_critical_filtration[int32_t]] out
    cdef vector[int32_t] f = vector[int32_t](filtrations.shape[1])
    out.reserve(filtrations.shape[0])
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[j] = filtrations[i,j]
        out.emplace_back(f)
    return out

cdef inline vector[Multi_critical_filtration[int32_t]] _py2vkc_i32(int32_t[:,:] filtrations) noexcept nogil:
    # cdef int32_t[:,:] filtrations = np.asarray(filtrations_, dtype=np.int32)
    cdef vector[Multi_critical_filtration[int32_t]] out
    cdef vector[int32_t] f = vector[int32_t](filtrations.shape[1])
    out.reserve(filtrations.shape[0])
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[j] = filtrations[i,j]
        out.emplace_back(f)
    return out

###### ------------------- CPP to PY

## tailored for Dynamic_multi_parameter_filtration
## testing finite or not is not necessary for Multi_parameter_filtration
## won't work for Degree_rips_filtration

## CYTHON BUG: using tuples here will cause some weird issues. 
cdef inline _ff21cview_i32(One_critical_filtration[int32_t]* x, bool copy=False):
  cdef Py_ssize_t num_parameters = dereference(x).num_parameters()
  if not dereference(x).is_finite():
    return np.full(shape=num_parameters, fill_value=dereference(x)(0,0))
  cdef int32_t[:] x_view = <int32_t[:num_parameters]>(&(dereference(x)(0,0)))
  return np.array(x_view) if copy else np.asarray(x_view)

cdef inline _ff21cview2_i32(int32_t* x, Py_ssize_t num_parameters, int duplicate, bool copy=False):
  if duplicate:
    return np.full(shape=duplicate, fill_value=dereference(x))
  cdef int32_t[:] x_view = <int32_t[:num_parameters]>(x)
  return np.array(x_view) if copy else np.asarray(x_view)

cdef inline _ff2kcview_i32(Multi_critical_filtration[int32_t]* x, bool copy=False):
  cdef Py_ssize_t k = dereference(x).num_generators()
  cdef Py_ssize_t p = dereference(x).num_parameters()
  if dereference(x).is_finite():
    duplicate = 0
  else:
    duplicate = p
  return [_ff21cview2_i32(&(dereference(x)(i,0)), p, duplicate, copy=copy) for i in range(k)]


cdef inline  _vff21cview_i32(vector[One_critical_filtration[int32_t]]& x, bool copy = False):
  cdef Py_ssize_t num_stuff = x.size()
  return [_ff21cview_i32(&(x[i]), copy=copy) for i in range(num_stuff)]

cdef inline  _vff2kcview_i32(vector[Multi_critical_filtration[int32_t]]& x, bool copy = False):
  cdef Py_ssize_t num_stuff = x.size()
  return [_ff2kcview_i32(&(x[i]), copy=copy) for i in range(num_stuff)]
###### ------------------- PY TO CPP
#### ---------- 

cdef inline vector[int64_t] _py2p_i64(int64_t[:] filtration) noexcept nogil:
    # TODO: Is there no directer way to convert a T[:] into a vector[T]?
    # A memcpy would be much quicker than a python/cython for loop...
    # With a continuous memory use, we could also pass the pointers as iterators if we have access to it?
    cdef vector[int64_t] f = vector[int64_t](len(filtration))
    for i in range(len(filtration)):
      f[i] = filtration[i]
    return f

cdef inline vector[int64_t] _py2p2_i64(int64_t[:,:] filtrations) noexcept nogil:
    cdef vector[int64_t] f = vector[int64_t](filtrations.shape[0] * filtrations.shape[1])
    k = 0
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[k] = filtrations[i,j]
          k = k + 1
    return f

cdef inline vector[Point[int64_t]] _py2vp_i64(int64_t[:,:] filtrations) noexcept nogil:
    cdef vector[Point[int64_t]] out
    cdef Point[int64_t] f = Point[int64_t](filtrations.shape[1])
    out.reserve(filtrations.shape[0])
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[j] = filtrations[i,j]
        out.emplace_back(f)
    return out

cdef inline Multi_critical_filtration[int64_t] _py2kc_i64(int64_t[:,:] filtrations) noexcept nogil:
    # cdef int64_t[:,:] filtrations = np.asarray(filtrations_, dtype=np.int64)
    cdef vector[int64_t] f = vector[int64_t](filtrations.shape[0] * filtrations.shape[1])
    cdef int k = 0;
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
            f[k] = filtrations[i,j]
            k = k + 1
    cdef Multi_critical_filtration[int64_t] out = Multi_critical_filtration[int64_t](f.begin(), f.end(), filtrations.shape[1])
    out.simplify()
    return out

cdef inline One_critical_filtration[int64_t] _py21c_i64(int64_t[:] filtration) noexcept nogil:
    cdef One_critical_filtration[int64_t] out = _py2p_i64(filtration)
    return out


cdef inline vector[One_critical_filtration[int64_t]] _py2v1c_i64(int64_t[:,:] filtrations) noexcept nogil:
    # cdef int64_t[:,:] filtrations = np.asarray(filtrations_, dtype=np.int64)
    cdef vector[One_critical_filtration[int64_t]] out
    cdef vector[int64_t] f = vector[int64_t](filtrations.shape[1])
    out.reserve(filtrations.shape[0])
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[j] = filtrations[i,j]
        out.emplace_back(f)
    return out

cdef inline vector[Multi_critical_filtration[int64_t]] _py2vkc_i64(int64_t[:,:] filtrations) noexcept nogil:
    # cdef int64_t[:,:] filtrations = np.asarray(filtrations_, dtype=np.int64)
    cdef vector[Multi_critical_filtration[int64_t]] out
    cdef vector[int64_t] f = vector[int64_t](filtrations.shape[1])
    out.reserve(filtrations.shape[0])
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[j] = filtrations[i,j]
        out.emplace_back(f)
    return out

###### ------------------- CPP to PY

## tailored for Dynamic_multi_parameter_filtration
## testing finite or not is not necessary for Multi_parameter_filtration
## won't work for Degree_rips_filtration

## CYTHON BUG: using tuples here will cause some weird issues. 
cdef inline _ff21cview_i64(One_critical_filtration[int64_t]* x, bool copy=False):
  cdef Py_ssize_t num_parameters = dereference(x).num_parameters()
  if not dereference(x).is_finite():
    return np.full(shape=num_parameters, fill_value=dereference(x)(0,0))
  cdef int64_t[:] x_view = <int64_t[:num_parameters]>(&(dereference(x)(0,0)))
  return np.array(x_view) if copy else np.asarray(x_view)

cdef inline _ff21cview2_i64(int64_t* x, Py_ssize_t num_parameters, int duplicate, bool copy=False):
  if duplicate:
    return np.full(shape=duplicate, fill_value=dereference(x))
  cdef int64_t[:] x_view = <int64_t[:num_parameters]>(x)
  return np.array(x_view) if copy else np.asarray(x_view)

cdef inline _ff2kcview_i64(Multi_critical_filtration[int64_t]* x, bool copy=False):
  cdef Py_ssize_t k = dereference(x).num_generators()
  cdef Py_ssize_t p = dereference(x).num_parameters()
  if dereference(x).is_finite():
    duplicate = 0
  else:
    duplicate = p
  return [_ff21cview2_i64(&(dereference(x)(i,0)), p, duplicate, copy=copy) for i in range(k)]


cdef inline  _vff21cview_i64(vector[One_critical_filtration[int64_t]]& x, bool copy = False):
  cdef Py_ssize_t num_stuff = x.size()
  return [_ff21cview_i64(&(x[i]), copy=copy) for i in range(num_stuff)]

cdef inline  _vff2kcview_i64(vector[Multi_critical_filtration[int64_t]]& x, bool copy = False):
  cdef Py_ssize_t num_stuff = x.size()
  return [_ff2kcview_i64(&(x[i]), copy=copy) for i in range(num_stuff)]
###### ------------------- PY TO CPP
#### ---------- 

cdef inline vector[float] _py2p_f32(float[:] filtration) noexcept nogil:
    # TODO: Is there no directer way to convert a T[:] into a vector[T]?
    # A memcpy would be much quicker than a python/cython for loop...
    # With a continuous memory use, we could also pass the pointers as iterators if we have access to it?
    cdef vector[float] f = vector[float](len(filtration))
    for i in range(len(filtration)):
      f[i] = filtration[i]
    return f

cdef inline vector[float] _py2p2_f32(float[:,:] filtrations) noexcept nogil:
    cdef vector[float] f = vector[float](filtrations.shape[0] * filtrations.shape[1])
    k = 0
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[k] = filtrations[i,j]
          k = k + 1
    return f

cdef inline vector[Point[float]] _py2vp_f32(float[:,:] filtrations) noexcept nogil:
    cdef vector[Point[float]] out
    cdef Point[float] f = Point[float](filtrations.shape[1])
    out.reserve(filtrations.shape[0])
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[j] = filtrations[i,j]
        out.emplace_back(f)
    return out

cdef inline Multi_critical_filtration[float] _py2kc_f32(float[:,:] filtrations) noexcept nogil:
    # cdef float[:,:] filtrations = np.asarray(filtrations_, dtype=np.float32)
    cdef vector[float] f = vector[float](filtrations.shape[0] * filtrations.shape[1])
    cdef int k = 0;
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
            f[k] = filtrations[i,j]
            k = k + 1
    cdef Multi_critical_filtration[float] out = Multi_critical_filtration[float](f.begin(), f.end(), filtrations.shape[1])
    out.simplify()
    return out

cdef inline One_critical_filtration[float] _py21c_f32(float[:] filtration) noexcept nogil:
    cdef One_critical_filtration[float] out = _py2p_f32(filtration)
    return out


cdef inline vector[One_critical_filtration[float]] _py2v1c_f32(float[:,:] filtrations) noexcept nogil:
    # cdef float[:,:] filtrations = np.asarray(filtrations_, dtype=np.float32)
    cdef vector[One_critical_filtration[float]] out
    cdef vector[float] f = vector[float](filtrations.shape[1])
    out.reserve(filtrations.shape[0])
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[j] = filtrations[i,j]
        out.emplace_back(f)
    return out

cdef inline vector[Multi_critical_filtration[float]] _py2vkc_f32(float[:,:] filtrations) noexcept nogil:
    # cdef float[:,:] filtrations = np.asarray(filtrations_, dtype=np.float32)
    cdef vector[Multi_critical_filtration[float]] out
    cdef vector[float] f = vector[float](filtrations.shape[1])
    out.reserve(filtrations.shape[0])
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[j] = filtrations[i,j]
        out.emplace_back(f)
    return out

###### ------------------- CPP to PY

## tailored for Dynamic_multi_parameter_filtration
## testing finite or not is not necessary for Multi_parameter_filtration
## won't work for Degree_rips_filtration

## CYTHON BUG: using tuples here will cause some weird issues. 
cdef inline _ff21cview_f32(One_critical_filtration[float]* x, bool copy=False):
  cdef Py_ssize_t num_parameters = dereference(x).num_parameters()
  if not dereference(x).is_finite():
    return np.full(shape=num_parameters, fill_value=dereference(x)(0,0))
  cdef float[:] x_view = <float[:num_parameters]>(&(dereference(x)(0,0)))
  return np.array(x_view) if copy else np.asarray(x_view)

cdef inline _ff21cview2_f32(float* x, Py_ssize_t num_parameters, int duplicate, bool copy=False):
  if duplicate:
    return np.full(shape=duplicate, fill_value=dereference(x))
  cdef float[:] x_view = <float[:num_parameters]>(x)
  return np.array(x_view) if copy else np.asarray(x_view)

cdef inline _ff2kcview_f32(Multi_critical_filtration[float]* x, bool copy=False):
  cdef Py_ssize_t k = dereference(x).num_generators()
  cdef Py_ssize_t p = dereference(x).num_parameters()
  if dereference(x).is_finite():
    duplicate = 0
  else:
    duplicate = p
  return [_ff21cview2_f32(&(dereference(x)(i,0)), p, duplicate, copy=copy) for i in range(k)]


cdef inline  _vff21cview_f32(vector[One_critical_filtration[float]]& x, bool copy = False):
  cdef Py_ssize_t num_stuff = x.size()
  return [_ff21cview_f32(&(x[i]), copy=copy) for i in range(num_stuff)]

cdef inline  _vff2kcview_f32(vector[Multi_critical_filtration[float]]& x, bool copy = False):
  cdef Py_ssize_t num_stuff = x.size()
  return [_ff2kcview_f32(&(x[i]), copy=copy) for i in range(num_stuff)]
###### ------------------- PY TO CPP
#### ---------- 

cdef inline vector[double] _py2p_f64(double[:] filtration) noexcept nogil:
    # TODO: Is there no directer way to convert a T[:] into a vector[T]?
    # A memcpy would be much quicker than a python/cython for loop...
    # With a continuous memory use, we could also pass the pointers as iterators if we have access to it?
    cdef vector[double] f = vector[double](len(filtration))
    for i in range(len(filtration)):
      f[i] = filtration[i]
    return f

cdef inline vector[double] _py2p2_f64(double[:,:] filtrations) noexcept nogil:
    cdef vector[double] f = vector[double](filtrations.shape[0] * filtrations.shape[1])
    k = 0
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[k] = filtrations[i,j]
          k = k + 1
    return f

cdef inline vector[Point[double]] _py2vp_f64(double[:,:] filtrations) noexcept nogil:
    cdef vector[Point[double]] out
    cdef Point[double] f = Point[double](filtrations.shape[1])
    out.reserve(filtrations.shape[0])
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[j] = filtrations[i,j]
        out.emplace_back(f)
    return out

cdef inline Multi_critical_filtration[double] _py2kc_f64(double[:,:] filtrations) noexcept nogil:
    # cdef double[:,:] filtrations = np.asarray(filtrations_, dtype=np.float64)
    cdef vector[double] f = vector[double](filtrations.shape[0] * filtrations.shape[1])
    cdef int k = 0;
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
            f[k] = filtrations[i,j]
            k = k + 1
    cdef Multi_critical_filtration[double] out = Multi_critical_filtration[double](f.begin(), f.end(), filtrations.shape[1])
    out.simplify()
    return out

cdef inline One_critical_filtration[double] _py21c_f64(double[:] filtration) noexcept nogil:
    cdef One_critical_filtration[double] out = _py2p_f64(filtration)
    return out


cdef inline vector[One_critical_filtration[double]] _py2v1c_f64(double[:,:] filtrations) noexcept nogil:
    # cdef double[:,:] filtrations = np.asarray(filtrations_, dtype=np.float64)
    cdef vector[One_critical_filtration[double]] out
    cdef vector[double] f = vector[double](filtrations.shape[1])
    out.reserve(filtrations.shape[0])
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[j] = filtrations[i,j]
        out.emplace_back(f)
    return out

cdef inline vector[Multi_critical_filtration[double]] _py2vkc_f64(double[:,:] filtrations) noexcept nogil:
    # cdef double[:,:] filtrations = np.asarray(filtrations_, dtype=np.float64)
    cdef vector[Multi_critical_filtration[double]] out
    cdef vector[double] f = vector[double](filtrations.shape[1])
    out.reserve(filtrations.shape[0])
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[j] = filtrations[i,j]
        out.emplace_back(f)
    return out

###### ------------------- CPP to PY

## tailored for Dynamic_multi_parameter_filtration
## testing finite or not is not necessary for Multi_parameter_filtration
## won't work for Degree_rips_filtration

## CYTHON BUG: using tuples here will cause some weird issues. 
cdef inline _ff21cview_f64(One_critical_filtration[double]* x, bool copy=False):
  cdef Py_ssize_t num_parameters = dereference(x).num_parameters()
  if not dereference(x).is_finite():
    return np.full(shape=num_parameters, fill_value=dereference(x)(0,0))
  cdef double[:] x_view = <double[:num_parameters]>(&(dereference(x)(0,0)))
  return np.array(x_view) if copy else np.asarray(x_view)

cdef inline _ff21cview2_f64(double* x, Py_ssize_t num_parameters, int duplicate, bool copy=False):
  if duplicate:
    return np.full(shape=duplicate, fill_value=dereference(x))
  cdef double[:] x_view = <double[:num_parameters]>(x)
  return np.array(x_view) if copy else np.asarray(x_view)

cdef inline _ff2kcview_f64(Multi_critical_filtration[double]* x, bool copy=False):
  cdef Py_ssize_t k = dereference(x).num_generators()
  cdef Py_ssize_t p = dereference(x).num_parameters()
  if dereference(x).is_finite():
    duplicate = 0
  else:
    duplicate = p
  return [_ff21cview2_f64(&(dereference(x)(i,0)), p, duplicate, copy=copy) for i in range(k)]


cdef inline  _vff21cview_f64(vector[One_critical_filtration[double]]& x, bool copy = False):
  cdef Py_ssize_t num_stuff = x.size()
  return [_ff21cview_f64(&(x[i]), copy=copy) for i in range(num_stuff)]

cdef inline  _vff2kcview_f64(vector[Multi_critical_filtration[double]]& x, bool copy = False):
  cdef Py_ssize_t num_stuff = x.size()
  return [_ff2kcview_f64(&(x[i]), copy=copy) for i in range(num_stuff)]
cdef inline KFlat_i32_2_python(KFlat_i32* x, bool copy=False, bool raw=False):
  cdef Py_ssize_t k = dereference(x).num_generators()


  cdef int num_parameters = 2

  cdef int32_t[:] data_view = <int32_t[:k]>(&(dereference(x)(0,0)))
  numpy_view = np.asarray(data_view, dtype=np.int32)
  if raw:
    return numpy_view
  return np.concatenate([numpy_view[:,None], np.arange(k, dtype=np.int32)[:,None]], axis=1)


cdef inline  vect_KFlat_i32_2_python(vector[KFlat_i32]& x, bool copy = False, bool raw=False):
  cdef Py_ssize_t num_stuff = x.size()
  return [KFlat_i32_2_python(&(x[i]), copy=copy, raw=raw) for i in range(num_stuff)]

cdef inline KFlat_i32 python_2_KFlat_i32(int32_t[:,:] filtrations) noexcept nogil:
    cdef vector[double] f = vector[double](filtrations.shape[0] * filtrations.shape[1])
    cdef int k = 0;
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
            f[k] = filtrations[i,j]
            k = k + 1
    cdef KFlat_i32 out = KFlat_i32(f.begin(), f.end(), filtrations.shape[1])
    out.simplify()
    return out

cdef inline vector[KFlat_i32] python_2_vect_KFlat_i32(int32_t[:,:] filtrations) noexcept nogil:
    # cdef double[:,:] filtrations = np.asarray(filtrations_, dtype=np.float64)
    cdef vector[KFlat_i32] out
    cdef vector[int32_t] f = vector[int32_t](filtrations.shape[1])
    out.reserve(filtrations.shape[0])
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[j] = filtrations[i,j]
        out.emplace_back(f)
    return out
cdef inline Flat_i32_2_python(Flat_i32* x, bool copy=False, bool raw=False):
  cdef Py_ssize_t k = dereference(x).num_generators()


  cdef int num_parameters = 2

  cdef int32_t[:] data_view = <int32_t[:k]>(&(dereference(x)(0,0)))
  numpy_view = np.asarray(data_view, dtype=np.int32)
  if raw:
    return numpy_view
  return np.concatenate([numpy_view[:,None], np.arange(k, dtype=np.int32)[:,None]], axis=1)


cdef inline  vect_Flat_i32_2_python(vector[Flat_i32]& x, bool copy = False, bool raw=False):
  cdef Py_ssize_t num_stuff = x.size()
  return [Flat_i32_2_python(&(x[i]), copy=copy, raw=raw) for i in range(num_stuff)]



cdef inline Flat_i32 python_2_Flat_i32(int32_t[:] filtration) noexcept nogil:
  cdef int num_parameters = filtration.shape[0]
  cdef Flat_i32 out = Flat_i32(num_parameters) 
  cdef int32_t* x
  for i in range(num_parameters):
    x = &out(0,i)
    x[0] = filtration[i]
  return out

cdef inline vector[Flat_i32] python_2_vect_Flat_i32(int32_t[:,:] filtrations) noexcept nogil:
    # cdef double[:,:] filtrations = np.asarray(filtrations_, dtype=np.float64)
    cdef vector[Flat_i32] out
    cdef vector[int32_t] f = vector[int32_t](filtrations.shape[1])
    out.reserve(filtrations.shape[0])
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[j] = filtrations[i,j]
        out.emplace_back(f)
    return out
cdef inline KFlat_f64_2_python(KFlat_f64* x, bool copy=False, bool raw=False):
  cdef Py_ssize_t k = dereference(x).num_generators()


  cdef int num_parameters = 2

  cdef double[:] data_view = <double[:k]>(&(dereference(x)(0,0)))
  numpy_view = np.asarray(data_view, dtype=np.float64)
  if raw:
    return numpy_view
  return np.concatenate([numpy_view[:,None], np.arange(k, dtype=np.float64)[:,None]], axis=1)


cdef inline  vect_KFlat_f64_2_python(vector[KFlat_f64]& x, bool copy = False, bool raw=False):
  cdef Py_ssize_t num_stuff = x.size()
  return [KFlat_f64_2_python(&(x[i]), copy=copy, raw=raw) for i in range(num_stuff)]

cdef inline KFlat_f64 python_2_KFlat_f64(double[:,:] filtrations) noexcept nogil:
    cdef vector[double] f = vector[double](filtrations.shape[0] * filtrations.shape[1])
    cdef int k = 0;
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
            f[k] = filtrations[i,j]
            k = k + 1
    cdef KFlat_f64 out = KFlat_f64(f.begin(), f.end(), filtrations.shape[1])
    out.simplify()
    return out

cdef inline vector[KFlat_f64] python_2_vect_KFlat_f64(double[:,:] filtrations) noexcept nogil:
    # cdef double[:,:] filtrations = np.asarray(filtrations_, dtype=np.float64)
    cdef vector[KFlat_f64] out
    cdef vector[double] f = vector[double](filtrations.shape[1])
    out.reserve(filtrations.shape[0])
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[j] = filtrations[i,j]
        out.emplace_back(f)
    return out
cdef inline Flat_f64_2_python(Flat_f64* x, bool copy=False, bool raw=False):
  cdef Py_ssize_t k = dereference(x).num_generators()


  cdef int num_parameters = 2

  cdef double[:] data_view = <double[:k]>(&(dereference(x)(0,0)))
  numpy_view = np.asarray(data_view, dtype=np.float64)
  if raw:
    return numpy_view
  return np.concatenate([numpy_view[:,None], np.arange(k, dtype=np.float64)[:,None]], axis=1)


cdef inline  vect_Flat_f64_2_python(vector[Flat_f64]& x, bool copy = False, bool raw=False):
  cdef Py_ssize_t num_stuff = x.size()
  return [Flat_f64_2_python(&(x[i]), copy=copy, raw=raw) for i in range(num_stuff)]



cdef inline Flat_f64 python_2_Flat_f64(double[:] filtration) noexcept nogil:
  cdef int num_parameters = filtration.shape[0]
  cdef Flat_f64 out = Flat_f64(num_parameters) 
  cdef double* x
  for i in range(num_parameters):
    x = &out(0,i)
    x[0] = filtration[i]
  return out

cdef inline vector[Flat_f64] python_2_vect_Flat_f64(double[:,:] filtrations) noexcept nogil:
    # cdef double[:,:] filtrations = np.asarray(filtrations_, dtype=np.float64)
    cdef vector[Flat_f64] out
    cdef vector[double] f = vector[double](filtrations.shape[1])
    out.reserve(filtrations.shape[0])
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[j] = filtrations[i,j]
        out.emplace_back(f)
    return out
cdef inline KContiguous_i32_2_python(KContiguous_i32* x, bool copy=False, bool raw=False):
  cdef Py_ssize_t k = dereference(x).num_generators()


  cdef Py_ssize_t p = dereference(x).num_parameters()
  if dereference(x).is_finite():
    duplicate = 0
  else:
    duplicate = p
  # TODO  : make it contiguous
  return [_ff21cview2_i32(&(dereference(x)(i,0)), p, duplicate, copy=copy) for i in range(k)]


cdef inline  vect_KContiguous_i32_2_python(vector[KContiguous_i32]& x, bool copy = False, bool raw=False):
  cdef Py_ssize_t num_stuff = x.size()
  return [KContiguous_i32_2_python(&(x[i]), copy=copy, raw=raw) for i in range(num_stuff)]

cdef inline KContiguous_i32 python_2_KContiguous_i32(int32_t[:,:] filtrations) noexcept nogil:
    cdef vector[double] f = vector[double](filtrations.shape[0] * filtrations.shape[1])
    cdef int k = 0;
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
            f[k] = filtrations[i,j]
            k = k + 1
    cdef KContiguous_i32 out = KContiguous_i32(f.begin(), f.end(), filtrations.shape[1])
    out.simplify()
    return out

cdef inline vector[KContiguous_i32] python_2_vect_KContiguous_i32(int32_t[:,:] filtrations) noexcept nogil:
    # cdef double[:,:] filtrations = np.asarray(filtrations_, dtype=np.float64)
    cdef vector[KContiguous_i32] out
    cdef vector[int32_t] f = vector[int32_t](filtrations.shape[1])
    out.reserve(filtrations.shape[0])
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[j] = filtrations[i,j]
        out.emplace_back(f)
    return out
# Assumes it's contiguous
cdef inline Contiguous_i32_2_python(Contiguous_i32* x, bool copy=False, bool raw=False):
  cdef Py_ssize_t num_parameters = dereference(x).num_parameters()
  if not dereference(x).is_finite():
    return np.full(shape=num_parameters, fill_value=dereference(x)(0,0))
  cdef int32_t[:] x_view = <int32_t[:num_parameters]>(&(dereference(x)(0,0)))
  return np.array(x_view) if copy else np.asarray(x_view)

cdef inline  vect_Contiguous_i32_2_python(vector[Contiguous_i32]& x, bool copy = False, bool raw=False):
  cdef Py_ssize_t num_stuff = x.size()
  return [Contiguous_i32_2_python(&(x[i]), copy=copy, raw=raw) for i in range(num_stuff)]



cdef inline Contiguous_i32 python_2_Contiguous_i32(int32_t[:] filtration) noexcept nogil:
  cdef int num_parameters = filtration.shape[0]
  cdef Contiguous_i32 out = Contiguous_i32(num_parameters) 
  cdef int32_t* x
  for i in range(num_parameters):
    x = &out(0,i)
    x[0] = filtration[i]
  return out

cdef inline vector[Contiguous_i32] python_2_vect_Contiguous_i32(int32_t[:,:] filtrations) noexcept nogil:
    # cdef double[:,:] filtrations = np.asarray(filtrations_, dtype=np.float64)
    cdef vector[Contiguous_i32] out
    cdef vector[int32_t] f = vector[int32_t](filtrations.shape[1])
    out.reserve(filtrations.shape[0])
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[j] = filtrations[i,j]
        out.emplace_back(f)
    return out
cdef inline KContiguous_f64_2_python(KContiguous_f64* x, bool copy=False, bool raw=False):
  cdef Py_ssize_t k = dereference(x).num_generators()


  cdef Py_ssize_t p = dereference(x).num_parameters()
  if dereference(x).is_finite():
    duplicate = 0
  else:
    duplicate = p
  # TODO  : make it contiguous
  return [_ff21cview2_f64(&(dereference(x)(i,0)), p, duplicate, copy=copy) for i in range(k)]


cdef inline  vect_KContiguous_f64_2_python(vector[KContiguous_f64]& x, bool copy = False, bool raw=False):
  cdef Py_ssize_t num_stuff = x.size()
  return [KContiguous_f64_2_python(&(x[i]), copy=copy, raw=raw) for i in range(num_stuff)]

cdef inline KContiguous_f64 python_2_KContiguous_f64(double[:,:] filtrations) noexcept nogil:
    cdef vector[double] f = vector[double](filtrations.shape[0] * filtrations.shape[1])
    cdef int k = 0;
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
            f[k] = filtrations[i,j]
            k = k + 1
    cdef KContiguous_f64 out = KContiguous_f64(f.begin(), f.end(), filtrations.shape[1])
    out.simplify()
    return out

cdef inline vector[KContiguous_f64] python_2_vect_KContiguous_f64(double[:,:] filtrations) noexcept nogil:
    # cdef double[:,:] filtrations = np.asarray(filtrations_, dtype=np.float64)
    cdef vector[KContiguous_f64] out
    cdef vector[double] f = vector[double](filtrations.shape[1])
    out.reserve(filtrations.shape[0])
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[j] = filtrations[i,j]
        out.emplace_back(f)
    return out
# Assumes it's contiguous
cdef inline Contiguous_f64_2_python(Contiguous_f64* x, bool copy=False, bool raw=False):
  cdef Py_ssize_t num_parameters = dereference(x).num_parameters()
  if not dereference(x).is_finite():
    return np.full(shape=num_parameters, fill_value=dereference(x)(0,0))
  cdef double[:] x_view = <double[:num_parameters]>(&(dereference(x)(0,0)))
  return np.array(x_view) if copy else np.asarray(x_view)

cdef inline  vect_Contiguous_f64_2_python(vector[Contiguous_f64]& x, bool copy = False, bool raw=False):
  cdef Py_ssize_t num_stuff = x.size()
  return [Contiguous_f64_2_python(&(x[i]), copy=copy, raw=raw) for i in range(num_stuff)]



cdef inline Contiguous_f64 python_2_Contiguous_f64(double[:] filtration) noexcept nogil:
  cdef int num_parameters = filtration.shape[0]
  cdef Contiguous_f64 out = Contiguous_f64(num_parameters) 
  cdef double* x
  for i in range(num_parameters):
    x = &out(0,i)
    x[0] = filtration[i]
  return out

cdef inline vector[Contiguous_f64] python_2_vect_Contiguous_f64(double[:,:] filtrations) noexcept nogil:
    # cdef double[:,:] filtrations = np.asarray(filtrations_, dtype=np.float64)
    cdef vector[Contiguous_f64] out
    cdef vector[double] f = vector[double](filtrations.shape[1])
    out.reserve(filtrations.shape[0])
    for i in range(filtrations.shape[0]):
        for j in range(filtrations.shape[1]):
          f[j] = filtrations[i,j]
        out.emplace_back(f)
    return out
