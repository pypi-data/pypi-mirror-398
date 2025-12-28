cdef class BasicHashable:
    cdef long cached_hash
    cdef bint hash_computed
    cdef readonly Py_ssize_t data_size
    cdef readonly bint __frozen__
    cdef readonly bint cacheable
    cdef long _compute_hash(self) # type: ignore