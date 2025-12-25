from libc.stdlib cimport free

cdef class _finalizer:
    cdef void *_obj

    def __cinit__(void * obj):
        _obj = obj
        
    def __dealloc__(self):
        if self._obj is not NULL:
            free(self._obj)
