cimport cython

@cython.boundscheck(False)  # Deactivate bounds checking
@cython.wraparound(False)   # Deactivate negative indexing.
cdef double mv_max(double [:] mv):
    cdef double output = mv[0]
    cdef double tmp
    cdef unsigned int i
    for i in range(1,mv.shape[0]):
        tmp = mv[i]
        if tmp > output:
            output = tmp

    return output

@cython.boundscheck(False)  # Deactivate bounds checking
@cython.wraparound(False)   # Deactivate negative indexing.
cdef double mv_min(double [:] mv):
    cdef double output = mv[0]
    cdef double tmp
    cdef unsigned int i
    for i in range(1,mv.shape[0]):
        tmp = mv[i]
        if tmp < output:
            output = tmp

    return output



@cython.boundscheck(False)  # Deactivate bounds checking
@cython.wraparound(False)   # Deactivate negative indexing.
cdef double mv_max2d(double [:,:] mv):
    cdef double output = mv[0,0]
    cdef double tmp
    cdef unsigned int i
    for i in range(0,mv.shape[0]):
        for j in range(0, mv.shape[1]):
            tmp = mv[i,j]
            if tmp > output:
                output = tmp

    return output

@cython.boundscheck(False)  # Deactivate bounds checking
@cython.wraparound(False)   # Deactivate negative indexing.
cdef double mv_min2d(double [:,:] mv):
    cdef double output = mv[0,0]
    cdef double tmp
    cdef unsigned int i
    for i in range(0,mv.shape[0]):
        for j in range(0, mv.shape[1]):
            tmp = mv[i,j]
            if tmp < output:
                output = tmp

    return output

@cython.boundscheck(False)  # Deactivate bounds checking
@cython.wraparound(False)   # Deactivate negative indexing.
cdef double mv_argmax(double [:] mv):
    cdef double output = mv[0]
    cdef double tmp
    cdef unsigned int index = 0
    cdef unsigned int i
    for i in range(1,mv.shape[0]):
        tmp = mv[i]
        if tmp > output:
            output = tmp
            index = i


    return index

@cython.boundscheck(False)  # Deactivate bounds checking
@cython.wraparound(False)   # Deactivate negative indexing.
cdef double mv_argmin(double [:] mv):
    cdef double output = mv[0]
    cdef double tmp
    cdef unsigned int index = 0
    cdef unsigned int i
    for i in range(1,mv.shape[0]):
        tmp = mv[i]
        if tmp < output:
            output = tmp
            index = i

    return index
