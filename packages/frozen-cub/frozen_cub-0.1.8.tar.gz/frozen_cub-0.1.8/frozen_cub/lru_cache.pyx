# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
# cython: initializedcheck=False
# cython: nonecheck=False

from cython cimport final
from libc.stdlib cimport malloc, calloc, free
from cpython.object cimport PyObject_Hash, PyObject, PyObject_RichCompareBool, Py_EQ
from cpython.ref cimport Py_INCREF, Py_DECREF
from .constants cimport FALSE, TRUE, FUNC_FAILURE, FUNC_SUCCESS

# ============================================================================
# Constants
# ============================================================================
cdef long EMPTY_KEY = <long>(-1)
cdef size_t NOT_FOUND = <size_t>(-1)
cdef size_t MIN_BUCKETS = <size_t>16
cdef size_t ZERO = <size_t>0
cdef size_t LOAD_FACTOR_NUM = <size_t>7    # Rehash when occupied > 7/10 of buckets
cdef size_t LOAD_FACTOR_DEN = <size_t>10
cdef size_t MIN_CAPACITY = <size_t>1
cdef size_t DEFAULT_CAPACITY = <size_t>512
cdef size_t MAX_CAPACITY = <size_t>1000000 # 1 million max capacity
cdef object MISSING = object()

# ============================================================================
# LRU Node - doubly linked list node with hash key and object value
# ============================================================================
cdef struct LRUNode:
    long key            # hash of the original key
    PyObject* orig_key  # original key object for equality comparison
    PyObject* value
    LRUNode* prev
    LRUNode* next
# ============================================================================
# Value helpers - encapsulate refcounting for PyObject* values
# ============================================================================
cdef inline void value_set(LRUNode* node, object val):
    Py_INCREF(val)
    node.value = <PyObject*>val


cdef inline void value_replace(LRUNode* node, object val):
    Py_DECREF(<object>node.value)
    Py_INCREF(val)
    node.value = <PyObject*>val


cdef inline object value_get(LRUNode* node):
    return <object>node.value


cdef inline void value_clear(LRUNode* node):
    if node.value:
        Py_DECREF(<object>node.value)
        node.value = NULL


# ============================================================================
# Key helpers - encapsulate refcounting for orig_key
# ============================================================================
cdef inline void key_set(LRUNode* node, object key):
    Py_INCREF(key)
    node.orig_key = <PyObject*>key


cdef inline void key_replace(LRUNode* node, object key):
    Py_DECREF(<object>node.orig_key)
    Py_INCREF(key)
    node.orig_key = <PyObject*>key


cdef inline object key_get(LRUNode* node):
    return <object>node.orig_key


cdef inline void key_clear(LRUNode* node):
    if node.orig_key:
        Py_DECREF(<object>node.orig_key)
        node.orig_key = NULL


cdef inline bool key_equals(LRUNode* node, object key):
    """Check if node's original key equals the given key."""
    return PyObject_RichCompareBool(<object>node.orig_key, key, Py_EQ) == 1


# ============================================================================
# Hash table entry - maps key to node pointer
# ============================================================================
cdef struct HashEntry:
    long key
    LRUNode* node
    bint is_tombstone


# ============================================================================
# Pure C LRU Cache structure
# ============================================================================
cdef struct CLRUCache:
    LRUNode* head           # Least recently used
    LRUNode* tail           # Most recently used
    HashEntry* buckets      # Hash table array
    size_t num_buckets      # Hash table size (always power of 2)
    size_t mask             # num_buckets - 1 for fast modulo
    size_t length           # Current number of entries
    size_t capacity         # Max entries before eviction
    size_t tombstones       # Count of tombstone slots

    # Node pool - pre-allocated nodes to avoid malloc/free per operation
    LRUNode* node_pool      # Pre-allocated array of nodes
    LRUNode* freelist       # Singly-linked list of free nodes

# ============================================================================
# Hash table operations
# ============================================================================
cdef inline size_t find_slot(CLRUCache* cache, long hash_key, object orig_key):
    """Find slot for key (either existing or first empty/tombstone)."""
    cdef size_t idx = <size_t>hash_key & cache.mask
    cdef size_t first_tombstone = NOT_FOUND
    cdef size_t checked = ZERO
    cdef HashEntry* entry

    while checked < cache.num_buckets:
        entry = &cache.buckets[idx] # type: ignore
        if entry.key == EMPTY_KEY:
            return first_tombstone if first_tombstone != NOT_FOUND else idx
        if entry.is_tombstone:
            if first_tombstone == NOT_FOUND:
                first_tombstone = idx
        elif entry.key == hash_key and key_equals(entry.node, orig_key):
            return idx
        idx = (idx + 1) & cache.mask
        checked += 1
    return first_tombstone if first_tombstone != NOT_FOUND else ZERO


cdef inline size_t find_empty_slot(CLRUCache* cache, long hash_key):
    """Find first empty slot for rehashing (fresh table has no tombstones)."""
    cdef size_t idx = <size_t>hash_key & cache.mask
    cdef size_t checked = ZERO

    while checked < cache.num_buckets:
        if cache.buckets[idx].key == EMPTY_KEY: # type: ignore
            return idx
        idx = (idx + 1) & cache.mask
        checked += 1
    return ZERO


cdef inline LRUNode* hash_get(CLRUCache* cache, long hash_key, object orig_key):
    """Get node pointer for key, or NULL if not found."""
    cdef size_t idx = <size_t>hash_key & cache.mask
    cdef size_t checked = ZERO
    cdef HashEntry* entry

    while checked < cache.num_buckets:
        entry = &cache.buckets[idx] # type: ignore
        if entry.key == EMPTY_KEY:
            return NULL # type: ignore
        if not entry.is_tombstone and entry.key == hash_key and key_equals(entry.node, orig_key):
            return entry.node
        idx = (idx + 1) & cache.mask
        checked += 1
    return NULL # type: ignore


cdef inline void hash_set(CLRUCache* cache, long hash_key, LRUNode* node):
    """Set key -> node mapping."""
    cdef size_t idx = find_slot(cache, hash_key, key_get(node))
    if cache.buckets[idx].is_tombstone: # type: ignore
        cache.tombstones -= 1
    cache.buckets[idx].key = hash_key # type: ignore
    cache.buckets[idx].node = node # type: ignore
    cache.buckets[idx].is_tombstone = FALSE # type: ignore


cdef inline void hash_delete(CLRUCache* cache, long hash_key, object orig_key):
    """Delete key from hash table (marks as tombstone)."""
    cdef size_t idx = <size_t>hash_key & cache.mask
    cdef size_t checked = ZERO
    cdef HashEntry* entry

    while checked < cache.num_buckets:
        entry = &cache.buckets[idx] # type: ignore
        if entry.key == EMPTY_KEY:
            return # type: ignore
        if not entry.is_tombstone and entry.key == hash_key and key_equals(entry.node, orig_key):
            entry.is_tombstone = TRUE
            entry.node = NULL
            cache.tombstones += 1
            return # type: ignore
        idx = (idx + 1) & cache.mask
        checked += 1


cdef inline Py_ssize_t hash_resize(CLRUCache* cache, size_t new_size):
    """Resize hash table. Returns 0 on success, -1 on failure."""
    cdef HashEntry* old_buckets = cache.buckets
    cdef size_t old_size = cache.num_buckets
    cdef HashEntry* new_buckets
    cdef size_t i = ZERO
    cdef size_t idx
    cdef HashEntry* entry

    new_buckets = <HashEntry*>calloc(new_size, sizeof(HashEntry)) # type: ignore
    if not new_buckets:
        return FUNC_FAILURE

    init_buckets(new_buckets, new_size)

    cache.buckets = new_buckets  # Swap in new table
    cache.num_buckets = new_size
    cache.mask = new_size - 1
    cache.tombstones = ZERO # Rehashing clears all tombstones

    if old_buckets: # Rehash old entries
        while i < old_size:
            entry = &old_buckets[i] # type: ignore
            if entry.key != EMPTY_KEY and not entry.is_tombstone:
                idx = find_empty_slot(cache, entry.key)
                cache.buckets[idx].key = entry.key # type: ignore
                cache.buckets[idx].node = entry.node # type: ignore
                cache.buckets[idx].is_tombstone = FALSE # type: ignore
            i += 1
        free(<void*>old_buckets)
    return FUNC_SUCCESS


# ============================================================================
# Initialization helpers
# ============================================================================
cdef inline void init_buckets(HashEntry* buckets, size_t count):
    cdef size_t i = ZERO
    while i < count:
        buckets[i].key = EMPTY_KEY # type: ignore
        buckets[i].node = NULL # type: ignore
        buckets[i].is_tombstone = FALSE # type: ignore
        i += 1


cdef inline void build_freelist(CLRUCache* cache):
    """Link all pool nodes into the freelist."""
    cache.freelist = &cache.node_pool[0] # type: ignore
    cdef size_t i = ZERO
    while i < cache.capacity - 1:
        cache.node_pool[i].next = &cache.node_pool[i + 1] # type: ignore
        i += 1
    cache.node_pool[cache.capacity - 1].next = NULL # type: ignore


# ============================================================================
# Node pool operations - avoid malloc/free per operation
# ============================================================================
cdef inline LRUNode* node_alloc(CLRUCache* cache, long hash_key, object orig_key, object value):
    """Get a node from freelist or return NULL if exhausted."""
    cdef LRUNode* node = cache.freelist
    if node:
        cache.freelist = node.next  # Pop from freelist (uses next as singly-linked)
        node.key = hash_key
        key_set(node, orig_key)
        value_set(node, value)
        node.prev = NULL
        node.next = NULL
    return node


cdef inline void node_release(CLRUCache* cache, LRUNode* node):
    """Return a node to the freelist, clearing key and value."""
    key_clear(node)
    value_clear(node)
    node.next = cache.freelist  # Push onto freelist
    cache.freelist = node


# ============================================================================
# Linked list operations
# ============================================================================


cdef inline void list_unlink(LRUNode* node, CLRUCache* cache):
    """Remove node from list without freeing."""
    if node.prev:
        node.prev.next = node.next
    else:
        cache.head = node.next
    if node.next:
        node.next.prev = node.prev
    else:
        cache.tail = node.prev
    node.prev = NULL
    node.next = NULL


cdef inline void list_push_back(LRUNode* node, CLRUCache* cache):
    """Add node to tail (most recently used)."""
    node.prev = cache.tail
    node.next = NULL
    if cache.tail:
        cache.tail.next = node
    else:
        cache.head = node
    cache.tail = node


cdef inline void list_move_to_end(LRUNode* node, CLRUCache* cache):
    """Move existing node to tail."""
    if node == cache.tail: # type: ignore
        return # type: ignore
    list_unlink(node, cache)
    list_push_back(node, cache)

# ============================================================================
# Cache operations
# ============================================================================
cdef inline CLRUCache* cache_create(size_t capacity):
    """Create a new LRU cache."""
    if capacity == 0 or capacity > MAX_CAPACITY:
        capacity = DEFAULT_CAPACITY

    cdef CLRUCache* cache = <CLRUCache*>malloc(sizeof(CLRUCache)) # type: ignore
    if not cache:
        return NULL # type: ignore

    cache.head = NULL
    cache.tail = NULL
    cache.length = ZERO
    cache.tombstones = ZERO
    cache.capacity = capacity

    # Start with table size = 2x capacity, minimum 16, power of 2
    cdef size_t buckets = MIN_BUCKETS
    while buckets < capacity * 2:
        buckets *= 2

    cache.num_buckets = buckets
    cache.mask = buckets - 1
    cache.buckets = <HashEntry*>calloc(buckets, sizeof(HashEntry)) # type: ignore

    if not cache.buckets:
        free(<void*>cache)
        return NULL # type: ignore

    # Pre-allocate node pool (capacity nodes - we never need more)
    cache.node_pool = <LRUNode*>calloc(capacity, sizeof(LRUNode)) # type: ignore
    if not cache.node_pool:
        free(<void*>cache.buckets)
        free(<void*>cache)
        return NULL # type: ignore

    build_freelist(cache)
    init_buckets(cache.buckets, buckets)
    return cache


cdef inline void cache_destroy(CLRUCache* cache):
    cdef LRUNode* node
    cdef LRUNode* next_node

    if not cache:
        return # type: ignore

    # Decref all stored keys and values before freeing
    node = cache.head
    while node:
        next_node = node.next
        key_clear(node)
        value_clear(node)
        node = next_node

    # Free the pre-allocated node pool (single free for all nodes!)
    if cache.node_pool:
        free(<void*>cache.node_pool)

    # Free hash table
    if cache.buckets:
        free(<void*>cache.buckets)

    free(<void*>cache)


cdef inline object cache_get(CLRUCache* cache, long hash_key, object orig_key, object default_val, bint* found):
    """Get value for key. Sets found[0] = True if found."""
    cdef LRUNode* node = hash_get(cache, hash_key, orig_key)

    if not node:
        found[0] = False # type: ignore
        return default_val

    # Move to end (most recently used)
    list_move_to_end(node, cache)
    found[0] = True # type: ignore
    return value_get(node)


cdef inline Py_ssize_t cache_set(CLRUCache* cache, long hash_key, object orig_key, object value):
    """Set key -> value. Returns 0 on success, -1 on failure."""
    cdef LRUNode* node = hash_get(cache, hash_key, orig_key)
    cdef LRUNode* old_head
    cdef long old_hash_key
    cdef object old_orig_key

    if node:
        value_replace(node, value)
        list_move_to_end(node, cache)
        return FUNC_SUCCESS

    if cache.length >= cache.capacity:
        # Evict LRU and reuse node directly (skip freelist)
        old_head = cache.head
        old_hash_key = old_head.key
        old_orig_key = key_get(old_head)
        list_unlink(old_head, cache)
        hash_delete(cache, old_hash_key, old_orig_key)

        # Rehash if tombstones + length exceed load factor
        if (cache.tombstones + cache.length) * LOAD_FACTOR_DEN > cache.num_buckets * LOAD_FACTOR_NUM:
            if hash_resize(cache, cache.num_buckets) != FUNC_SUCCESS:
                return FUNC_FAILURE

        # Reuse evicted node with new key/value (replace handles decref of old)
        old_head.key = hash_key
        key_replace(old_head, orig_key)
        value_replace(old_head, value)
        hash_set(cache, hash_key, old_head)
        list_push_back(old_head, cache)
        return FUNC_SUCCESS

    # No eviction needed - get node from pool
    # Doubling rarely triggers: table starts at 2x capacity, so we hit capacity before 70% load
    if (cache.tombstones + cache.length) * LOAD_FACTOR_DEN > cache.num_buckets * LOAD_FACTOR_NUM:
        if hash_resize(cache, cache.num_buckets * 2) != FUNC_SUCCESS:
            return FUNC_FAILURE

    node = node_alloc(cache, hash_key, orig_key, value)
    if not node:
        return FUNC_FAILURE

    hash_set(cache, hash_key, node)
    list_push_back(node, cache)
    cache.length += 1
    return FUNC_SUCCESS


cdef inline bint cache_has(CLRUCache* cache, long hash_key, object orig_key):
    cdef LRUNode* node = hash_get(cache, hash_key, orig_key)
    return node != NULL # type: ignore


cdef inline bint cache_delete(CLRUCache* cache, long hash_key, object orig_key):
    """Delete key. Returns True if deleted, False if not found."""
    cdef LRUNode* node = hash_get(cache, hash_key, orig_key)

    if not node:
        return FALSE

    list_unlink(node, cache)
    hash_delete(cache, hash_key, orig_key)
    node_release(cache, node)  # Return to pool instead of free()
    cache.length -= 1
    return TRUE


cdef inline void cache_clear(CLRUCache* cache):
    """Clear all entries."""
    cdef LRUNode* node = cache.head
    cdef LRUNode* next_node

    # Clear all keys and values to decref them
    while node:
        next_node = node.next
        key_clear(node)
        value_clear(node)
        node = next_node

    cache.head = NULL
    cache.tail = NULL
    cache.length = ZERO
    cache.tombstones = ZERO
    build_freelist(cache)
    init_buckets(cache.buckets, cache.num_buckets)


# ============================================================================
# Thread safety - pthread mutex
# ============================================================================
cdef extern from "pthread.h" nogil:
    ctypedef struct pthread_mutex_t:
        pass
    int pthread_mutex_init(pthread_mutex_t*, void*)
    int pthread_mutex_lock(pthread_mutex_t*)
    int pthread_mutex_unlock(pthread_mutex_t*)
    int pthread_mutex_destroy(pthread_mutex_t*)


# ============================================================================
# Python wrapper class
# ============================================================================


@final
cdef class LRUCache:
    """
    High-performance LRU cache with integer keys and values.

    All core operations are O(1) and run without Python API calls.
    """
    cdef CLRUCache* _cache
    cdef bint thread_safe
    cdef pthread_mutex_t _mutex

    def __cinit__(self):
        pthread_mutex_init(&self._mutex, <void*>NULL)
        self._cache = NULL
    
    def __dealloc__(self):
        if self._cache:
            cache_destroy(self._cache)
        pthread_mutex_destroy(&self._mutex)
    
    def __init__(self, size_t capacity, bint thread_safe=FALSE):
        self.thread_safe = thread_safe
        self._cache = cache_create(capacity)
        if not self._cache:
            raise MemoryError("Failed to allocate LRU cache")
    
    cdef inline void _lock(self):
        if self.thread_safe:
            pthread_mutex_lock(&self._mutex)
    
    cdef inline void _unlock(self):
        if self.thread_safe:
            pthread_mutex_unlock(&self._mutex)
    
    cpdef void clear(self):
        """Remove all entries."""
        self._lock()
        cache_clear(self._cache)
        self._unlock()

    cpdef size_t length(self):
        """Return number of entries."""
        return self._cache.length

    # ========================================================================
    # Internal API (cdef) - hash + original key
    # ========================================================================
    cdef bint _has(self, long hash_key, object orig_key):
        cdef bint result
        self._lock()
        result = cache_has(self._cache, hash_key, orig_key)
        self._unlock()
        return result

    cdef object _get(self, long hash_key, object orig_key, object default = MISSING):
        cdef bint found
        cdef object result
        self._lock()
        result = cache_get(self._cache, hash_key, orig_key, default, &found)
        self._unlock()
        return result

    cdef void _set(self, long hash_key, object orig_key, object value):
        self._lock()
        if cache_set(self._cache, hash_key, orig_key, value) != FUNC_SUCCESS:
            self._unlock()
            raise MemoryError("Failed to insert into LRU cache")
        self._unlock()

    cdef void _delete(self, long hash_key, object orig_key):
        self._lock()
        cache_delete(self._cache, hash_key, orig_key)
        self._unlock()

    cdef object _pop(self, long hash_key, object orig_key, object default = MISSING):
        cdef LRUNode* node
        cdef object value
        self._lock()
        node = hash_get(self._cache, hash_key, orig_key)
        if node:
            value = value_get(node)
            Py_INCREF(value)  # Keep alive before node_release decrefs it
            list_unlink(node, self._cache)
            hash_delete(self._cache, hash_key, orig_key)
            node_release(self._cache, node)
            self._cache.length -= 1
            self._unlock()
            return value  # Cython will decref on return, balancing our incref
        self._unlock()
        return default

    # ========================================================================
    # Public API - accepts any hashable, uses PyObject_Hash internally
    # ========================================================================
    cpdef bint has(self, object key):
        """Check if hashable key exists."""
        return self._has(PyObject_Hash(key), key)

    cpdef object get(self, object key, object default=None):
        """Get value for hashable key, moving it to most-recently-used."""
        cdef long temp_hash = PyObject_Hash(key)
        cdef object result = self._get(temp_hash, key, default)
        if result is MISSING:
            return default
        return result

    cpdef void set(self, object key, object value):
        """Set hashable key -> value, evicting LRU if at capacity."""
        self._set(PyObject_Hash(key), key, value)

    cpdef void delete(self, object key):
        """Delete hashable key if it exists."""
        self._delete(PyObject_Hash(key), key)

    cpdef object pop(self, object key, object default=None):
        """Remove and return value for hashable key."""
        return self._pop(PyObject_Hash(key), key, default)

    # ========================================================================
    # Int API - DEPRECATED, kept for compatibility but uses key as its own orig_key
    # ========================================================================
    cpdef bint has_int(self, long key):
        return self._has(key, key)

    cpdef object get_int(self, long key, object default=None):
        return self._get(key, key, default)

    cpdef void set_int(self, long key, object value):
        self._set(key, key, value)

    cpdef void delete_int(self, long key):
        self._delete(key, key)

    cpdef object pop_int(self, long key, object default=None):
        return self._pop(key, key, default)

    cdef list _collect_keys(self):
        """Collect all original keys into a list (caller must hold lock if thread_safe)."""
        cdef LRUNode* current = self._cache.head
        cdef list keys = []

        while current:
            keys.append(key_get(current))
            current = current.next
        return keys

    def keys(self):
        """Return keys in LRU order."""
        self._lock()
        cdef list result = self._collect_keys()
        self._unlock()
        return result

    cdef list _collect_values(self):
        """Collect all values into a list (caller must hold lock if thread_safe)."""
        cdef LRUNode* current = self._cache.head
        cdef list vals = []

        while current:
            vals.append(value_get(current))
            current = current.next
        return vals

    cdef list _collect_items(self):
        """Collect all (key, value) pairs into a list (caller must hold lock if thread_safe)."""
        cdef LRUNode* current = self._cache.head
        cdef list result = []

        while current:
            result.append((key_get(current), value_get(current)))
            current = current.next
        return result

    def values(self):
        """Return values in LRU order."""
        self._lock()
        cdef list result = self._collect_values()
        self._unlock()
        return result

    def items(self):
        """Return (key, value) pairs in LRU order."""
        self._lock()
        cdef list result = self._collect_items()
        self._unlock()
        return result

    @property
    def capacity(self):
        return self._cache.capacity

    @property
    def head(self):
        """Least recently used key, or None if empty."""
        if not self._cache.head:
            return None
        return key_get(self._cache.head)

    @property
    def tail(self):
        """Most recently used key, or None if empty."""
        if not self._cache.tail:
            return None
        return key_get(self._cache.tail)

    def __reduce__(self):
        raise TypeError("LRUCache cannot be pickled")

    def __contains__(self, object key):
        return self.has(key)
    
    def __len__(self):
        return self._cache.length

    def __getitem__(self, object key):
        cdef object result = self.get(key, MISSING)
        if result is MISSING:
            raise KeyError(key)
        return result

    def __setitem__(self, object key, object value):
        self.set(key, value)

    def __delitem__(self, object key):
        if self.pop(key, MISSING) is MISSING:
            raise KeyError(key)
    
    def __iter__(self):
        """Iterate keys in LRU order (least recent first)."""
        self._lock()
        cdef list keys = self._collect_keys()
        self._unlock()
        return iter(keys)