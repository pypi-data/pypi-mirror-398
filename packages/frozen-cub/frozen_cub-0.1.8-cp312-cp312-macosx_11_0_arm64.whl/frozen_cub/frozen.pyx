"""Cython implementation of an immutable FrozenDict."""
from __future__ import annotations
from cpython.dict cimport PyDict_Keys, PyDict_Next, PyDict_Size, PyDict_New, PyDict_SetItem, PyDict_GetItem, PyDict_Items, PyDict_Values, PyDict_Check
from cpython.object cimport PyObject, PyObject_Hash, PyObject_IsInstance
from cython cimport final
from cpython.list cimport PyList_New, PyList_SET_ITEM, PyList_Size, PyList_Check, PyList_GET_ITEM
from cpython.tuple cimport PyTuple_New, PyTuple_SET_ITEM, PyTuple_Size, PyTuple_GET_ITEM, PyTuple_Check
from cpython.set cimport  PyFrozenSet_Check, PySet_Contains, PySet_New, PySet_Size, PySet_Check, PyFrozenSet_New, PySet_Add
from cpython.ref cimport Py_INCREF
from cpython.unicode cimport PyUnicode_Check
from cpython.bytes cimport PyBytes_Check
from cpython.long cimport PyLong_Check
from cpython.float cimport PyFloat_Check
from cpython.bool cimport PyBool_Check
from frozen_cub.utils cimport BasicHashable
from .constants cimport  FALSE, TRUE, PY_ZERO, THIRTY_ONE, ZERO

cdef inline bint _is_primitive(object obj):
    """Check if the object is a primitive type."""
    if obj is None:
        return TRUE
    if PyBool_Check(obj):
        return TRUE
    if PyUnicode_Check(obj):
        return TRUE
    if PyBytes_Check(obj):
        return TRUE
    if PyLong_Check(obj):
        return TRUE
    if PyFloat_Check(obj):
        return TRUE
    return FALSE

cpdef bint is_primitive(object obj):
    return _is_primitive(obj)

cdef inline bint already_frozen(object obj):
    return PyObject_IsInstance(obj, BasicHashable)


cdef inline object to_frozen_dict(dict obj, bint return_tuples = FALSE):
    """Create a new dict from the given object."""
    cdef tuple items, item
    cdef Py_ssize_t size, index
    cdef object key, value
    size = PyDict_Size(obj)
    items = PyTuple_New(size)
    index = PY_ZERO
    for key, value in PyDict_Items(obj):
        item = (key, _freeze(value))
        Py_INCREF(item)
        PyTuple_SET_ITEM(items, index, item)
        index += 1
    if return_tuples:
        return items
    return FrozenDict(items) # type: ignore

cdef inline tuple to_frozen_list(list obj):
    """Create a new tuple of frozen items from the given list."""
    cdef tuple items
    cdef Py_ssize_t size, index
    cdef object value
    size = PyList_Size(obj)
    items = PyTuple_New(size)
    index = PY_ZERO
    while index < size:
        value = _freeze(<object>PyList_GET_ITEM(obj, index))
        Py_INCREF(value)
        PyTuple_SET_ITEM(items, index, value)
        index += 1
    return items

cdef inline object to_frozen_set(set obj):
    """Create a new frozenset of frozen items from the given set."""
    cdef list frozen_items
    cdef Py_ssize_t index
    cdef object item
    frozen_items = PyList_New(PySet_Size(obj))
    index = PY_ZERO
    for item in obj:
        item = _freeze(item)
        Py_INCREF(item)
        PyList_SET_ITEM(frozen_items, index, item)
        index += 1
    return PyFrozenSet_New(frozen_items)

cdef inline tuple freeze_tuple_items(tuple obj):
    """Check and freeze each item in the tuple."""
    cdef Py_ssize_t size, index
    cdef object value
    size = PyTuple_Size(obj)
    cdef tuple frozen_items = PyTuple_New(size)
    index = PY_ZERO
    while index < size:
        value = _freeze(<object>PyTuple_GET_ITEM(obj, index))
        Py_INCREF(value)
        PyTuple_SET_ITEM(frozen_items, index, value)
        index += 1
    return frozen_items

cdef object _freeze(object obj, bint return_tuples = FALSE):
    """Internal freeze function to handle various types."""
    if _is_primitive(obj):
        return obj
    if already_frozen(obj):
        return obj
    if PyTuple_Check(obj):
        return freeze_tuple_items(obj) # type: ignore Pyright isn't recognizing PyTuple_Check
    if PyDict_Check(obj):
        return to_frozen_dict(obj, return_tuples) # type: ignore Pyright isn't recognizing PyDict_Check
    if PyList_Check(obj):
        return to_frozen_list(obj) # type: ignore Pyright isn't recognizing PyList_Check
    if PySet_Check(obj):
        return to_frozen_set(obj) # type: ignore Pyright isn't recognizing PySet_Check
    return obj

cpdef freeze(object obj):
    """Freeze an object by making it immutable and thus hashable."""
    return _freeze(obj)

@final
cdef class FrozenDict(BasicHashable):
    """An immutable and hashable dictionary."""
    cdef readonly dict data
    cdef readonly object _list_keys
    cdef readonly set _keys
    cdef readonly object _values
    cdef readonly object _items

    def __cinit__(self, object data = None):
        self.data = PyDict_New()
        self.data_size = PY_ZERO
        self._keys = PySet_New(<object>NULL)
        self._list_keys = None
        self._values = None
        self._items = None

        if data is None:
            return
        
        if PyDict_Check(data):
           data = _freeze(data, TRUE) # Ideally we are tuple[tuple[Any, Any], ...] by now

        for k, v in data: # type:ignore[arg-type]
            PySet_Add(self._keys, k)
            PyDict_SetItem(self.data, k, _freeze(v))
        self.data_size = PyDict_Size(self.data)
        
    def __init__(self, object data = None):
        """Initialize a FrozenDict from an existing mapping or iterable of key-value pairs.

        Accepts:
        - None (empty FrozenDict)
        - dict (values are recursively frozen)
        - iterable of (key, value) tuples
        """
        pass

    cdef object _get(self, object key, object default=None):
        if not PySet_Contains(self._keys, key):
            return default
        value = PyDict_GetItem(self.data, key)
        if value is not NULL:
            return <object>value
        return default

    cpdef object get(self, object key, object default=None):
        return self._get(key, default)

    cpdef list keys(self):
        if self._list_keys is None:
            self._list_keys = list(PyDict_Keys(self.data))
        return self._list_keys # type: ignore
    
    cpdef list values(self):
        if self._values is None:
            self._values = list(PyDict_Values(self.data))
        return self._values # type: ignore

    cpdef list items(self):
        if self._items is None:
            self._items = list(PyDict_Items(self.data))
        return self._items # type: ignore

    cdef long _compute_hash(self):
        cdef Py_ssize_t pos = PY_ZERO
        cdef long result = ZERO
        cdef long key_hash, value_hash, pair_hash
        cdef PyObject* key_ptr
        cdef PyObject* value_ptr

        if self.data_size == PY_ZERO:
            return <long>PyObject_Hash(())

        while PyDict_Next(self.data, &pos, &key_ptr, &value_ptr):
            key_hash = PyObject_Hash(<object>key_ptr)
            value_hash = PyObject_Hash(<object>value_ptr)
            pair_hash = key_hash ^ (value_hash * THIRTY_ONE)
            result ^= pair_hash
        return result

    cdef bool _contains(self, object key):
        return bool(PySet_Contains(self._keys, key))

    cpdef long get_hash(self):
        return self._compute_hash()

    def __eq__(self, other) -> bool:
        if not isinstance(other, FrozenDict): # type: ignore | Pyright doesn't understand this in Cython
            return False
        if self.data_size != other.data_size:
            return False
        return self.data == other.data

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> long:
        if not self.hash_computed:
            self.cached_hash = self._compute_hash()
            self.hash_computed = TRUE
        return self.cached_hash
    
    def __contains__(self, key) -> bool:
        return self._contains(key)
    
    def __iter__(self):
        return iter(self.keys())

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.data})"

    def __str__(self) -> str:
        return self.__repr__()

    def __getitem__(self, key) -> object:
        if not self._contains(key):
            raise KeyError(key)
        return self._get(key)
    
    def __len__(self) -> int:
        return <int>self.data_size
