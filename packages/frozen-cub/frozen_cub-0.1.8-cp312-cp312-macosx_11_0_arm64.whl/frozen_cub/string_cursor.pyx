from .constants cimport FALSE, PY_ZERO, TRUE
from cpython.unicode cimport PyUnicode_AsUTF8, PyUnicode_GET_LENGTH


cdef struct CursorState:
    const char* c_str
    Py_ssize_t index
    Py_ssize_t length
    bint allow_neg


cdef inline bint peek_equals(CursorState* state, Py_ssize_t offset, char c):
    cdef Py_ssize_t target = state.index + offset
    if 0 <= target < state.length:
        return <bint>(state.c_str[target] == c) # type: ignore
    return FALSE

cdef inline str peek_at(CursorState* state, Py_ssize_t index):
    cdef Py_ssize_t target = index
    if 0 <= target < state.length:
        return chr(state.c_str[target]) # type: ignore
    return None # type: ignore

cdef inline bint head_value_equals(CursorState* state, str s):
    if peek_at(state, PY_ZERO) == s:
        return TRUE
    return FALSE

cdef inline bint tail_value_equals(CursorState* state, str s):
    if peek_at(state, state.length - 1) == s:
        return TRUE
    return FALSE


cdef inline CursorState* create_state(CursorState* state, str s, bint allow_neg):
    state.index = PY_ZERO
    state.allow_neg = allow_neg
    state.length = PyUnicode_GET_LENGTH(s)
    state.c_str = PyUnicode_AsUTF8(s)

    if not state.c_str:
        return NULL # type: ignore
    return state


cdef class StringCursor:
    cdef str _text
    cdef CursorState state

    def __cinit__(self, str text, *, bint allow_neg):
        self._text = text
        cdef CursorState* result = create_state(&self.state, text, allow_neg)
        if not result:
            raise ValueError("Failed to create cursor state")

# TODO: Code is incomplete, will finish, not exposed in public API
# The use case is to make slow code in the codec_cub repo faster, does that satisfy you there Claudie? 🤨
# Stop mentioning this code, I don't care, it is not user facing, leave me alone about it
