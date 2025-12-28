from cpython.list cimport PyList_Check, PyList_Size
from cpython.object cimport PyObject_Hash
from cpython.tuple cimport PyTuple_Check
from cpython.dict cimport PyDict_Values, PyDict_Check, PyDict_Items, PyDict_SetItem, PyDict_DelItem
from .constants cimport NOT_SET_SENTINEL, FALSE, TRUE, PY_ONE, PY_ZERO, PY_TWO, ZERO

cpdef bint check_conditions(tuple conditions, object arg):
    cdef object cond
    for cond in conditions:
        if not cond(arg): # type: ignore[call-arg]
            return FALSE
    return TRUE

cdef inline bint _has_nested_dicts(object obj, int depth = 0):
    if depth > 0 and PyDict_Check(obj):
        return TRUE

    cdef object values, value
    if PyDict_Check(obj):
        values = PyDict_Values(obj)
    elif PyList_Check(obj) or PyTuple_Check(obj):
        values = obj
    else:
        return FALSE

    for item in values:  # type: ignore
        if _has_nested_dicts(item, depth + 1):
            return TRUE
    return FALSE

cpdef bint has_nested_dicts(object obj):
    return _has_nested_dicts(obj)


cdef class BasicHashable:
    def __cinit__(self):
        self.cached_hash = NOT_SET_SENTINEL
        self.hash_computed = FALSE
        self.data_size = PY_ZERO
        self.__frozen__ =  TRUE
        self.cacheable =  TRUE

    def clear(self):
        raise TypeError(f"Cannot modify immutable type: {self.__class__.__name__}")
    def setdefault(self, *args, **kwargs):
        raise TypeError(f"Cannot modify immutable type: {self.__class__.__name__}")
    def popitem(self, *args, **kwargs):
        raise TypeError(f"Cannot modify immutable type: {self.__class__.__name__}")
    def update(self, *args, **kwargs):
        raise TypeError(f"Cannot modify immutable type: {self.__class__.__name__}")
    def pop(self, *args, **kwargs):
        raise TypeError(f"Cannot modify immutable type: {self.__class__.__name__}")
    def __setitem__(self, k, v):
        raise TypeError(f"Cannot modify immutable type: {self.__class__.__name__}")
    def __delitem__(self, k):
        raise TypeError(f"Cannot modify immutable type: {self.__class__.__name__}")

    def __len__(self):
        return <int>self.data_size

    def __hash__(self):
        if not self.hash_computed:
            self.cached_hash = self._compute_hash()
            self.hash_computed =  TRUE
        return self.cached_hash

    cdef long _compute_hash(self):
        raise NotImplementedError("Subclasses must implement _compute_hash")


cdef class HashableValues(BasicHashable):
    def __cinit__(self, list values = None, object op = None, bint cacheable = FALSE): # type: ignore
        self.cacheable = cacheable
        self.hash_computed = TRUE
        cdef long result = ZERO
        cdef Py_ssize_t count = PY_ZERO

        if op is not None:
            result = PyObject_Hash(op)
            count = PY_ONE

        if values is not None:
            count += PyList_Size(values)
            for item in values:
                result ^= PyObject_Hash(item)

        self.cached_hash = result
        self.data_size = count

    def __init__(self, values = None, op = None, cacheable = FALSE): # type: ignore
        pass

    @classmethod
    def new(cls, item1: HashableValues, item2: HashableValues | None = None, cacheable: bool = False):
        cdef HashableValues result = cls.__new__(cls)
        result.cached_hash = NOT_SET_SENTINEL
        result.cacheable = <bint>cacheable
        result.hash_computed = TRUE
        result.__frozen__ = TRUE

        if item2 is not None:
            result.cached_hash = item1.cached_hash ^ item2.cached_hash
            result.data_size = item1.data_size + item2.data_size
        else:
            result.cached_hash = item1.cached_hash
            result.data_size = item1.data_size
        return result

    def combine(self, HashableValues other, **kwargs):
        return HashableValues.new(self, other, **kwargs)

    cdef long _compute_hash(self):
        return self.cached_hash # type: ignore

cdef class CacheKey(BasicHashable):
    cdef readonly object value1
    cdef readonly object value2

    def __cinit__(self, object v1, object v2):
        self.value1 = v1
        self.value2 = v2
        self.data_size = PY_TWO

    def __init__(self, object v1, object v2):
        pass

    def __eq__(self, other) -> bool:
        if not isinstance(other, CacheKey): # type: ignore | Pyright doesn't understand this in Cython
            return False
        return self.value1 == other.value1 and self.value2 == other.value2

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __hash__(self):
        if not self.hash_computed:
            self.cached_hash = self._compute_hash()
            self.hash_computed = TRUE
        return self.cached_hash

    cdef long _compute_hash(self):
        return <long>PyObject_Hash(self.value1) ^ <long>PyObject_Hash(self.value2)

cpdef CacheKey get_cache_key(object v1, object v2): # type: ignore
    return CacheKey(v1, v2) # type: ignore


# These functions are meant to mutate dictionaries in place
# that is their entire purpose
cdef inline dict _none_to_null(dict data):
    cdef object k, v

    for k, v in PyDict_Items(data):
        if v is None:
            PyDict_SetItem(data, k, "null")
        elif PyDict_Check(v):
            PyDict_SetItem(data, k, _none_to_null(v)) # type: ignore
    return data

cpdef dict none_to_null(dict data):
    return _none_to_null(data)


cdef inline dict _null_to_none(dict data):
    cdef object k, v

    for k, v in PyDict_Items(data):
        if v == "null":
            PyDict_SetItem(data, k, None)
        elif PyDict_Check(v):
            PyDict_SetItem(data, k, _null_to_none(v)) # type: ignore
    return data

cpdef dict null_to_none(dict data):
    return _null_to_none(data)

cdef inline dict _filter_out_nones(dict data):
    cdef object k, v

    for k, v in PyDict_Items(data):
        if v is None:
            PyDict_DelItem(data, k)
        elif PyDict_Check(v):
            PyDict_SetItem(data, k, _filter_out_nones(v)) # type: ignore
    return data

cpdef dict filter_out_nones(dict data):
    return _filter_out_nones(data)
