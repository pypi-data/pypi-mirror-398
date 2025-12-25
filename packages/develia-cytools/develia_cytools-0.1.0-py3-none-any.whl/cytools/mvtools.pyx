import cython


@cython.boundscheck(False)  # Deactivate bounds checking
@cython.wraparound(False)   # Deactivate negative indexing.
cpdef void copy(double [:] source,int src_offset,
                double [:] destination,int dst_offset,
                int count) except -1:

    cdef int i = 0
    for i in range(count):
        destination[i+dst_offset] = source[i+src_offset]

@cython.boundscheck(False)  # Deactivate bounds checking
@cython.wraparound(False)   # Deactivate negative indexing.
cpdef void apply(double [:] target, fn) except -1:

    for i in range(target.shape[0]):
        target[i] = fn(target[i])
