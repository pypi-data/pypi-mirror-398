# fractionals.pxd
# Cython definitions for GMP and Fraction class

from libc.stdlib cimport free

cdef extern from "gmp.h":
    # GMP rational
    ctypedef struct __mpq_struct: pass
    ctypedef __mpq_struct mpq_t[1]
    ctypedef __mpq_struct* mpq_ptr
    ctypedef const __mpq_struct* mpq_srcptr

    # GMP integer
    ctypedef struct __mpz_struct: pass
    ctypedef __mpz_struct mpz_t[1]
    ctypedef __mpz_struct* mpz_ptr
    ctypedef const __mpz_struct* mpz_srcptr

    # mpq functions
    void mpq_init(mpq_t x)
    void mpq_clear(mpq_t x)
    void mpq_set(mpq_t rop, mpq_srcptr op)
    void mpq_set_si(mpq_t rop, long num, unsigned long den)
    int mpq_set_str(mpq_t rop, const char* str, int base)
    void mpq_canonicalize(mpq_t rop)
    int mpq_cmp(mpq_t op1, mpq_t op2)
    void mpq_add(mpq_t rop, mpq_srcptr op1, mpq_srcptr op2)
    void mpq_sub(mpq_t rop, mpq_srcptr op1, mpq_srcptr op2)
    void mpq_mul(mpq_t rop, mpq_srcptr op1, mpq_srcptr op2)
    void mpq_div(mpq_t rop, mpq_srcptr op1, mpq_srcptr op2)
    char* mpq_get_str(char* str, int base, mpq_t op)
    mpz_ptr mpq_numref(mpq_t op)
    mpz_ptr mpq_denref(mpq_t op)
    char* mpz_get_str(char* str, int base, mpz_t op)
    void mpq_set_num(mpq_t rop, mpz_t num)
    void mpq_set_den(mpq_t rop, mpz_t den)

    # mpz functions for big ints
    void mpz_init(mpz_t x)
    void mpz_clear(mpz_t x)
    int mpz_set_str(mpz_t rop, const char* str, int base)

# Fraction class definition for Cython
cdef class Fraction:
    cdef mpq_t value
    cdef void _set_from_bigints(self, object num, object den)
    cdef void _set_from_object(self, object a)
    cdef Fraction _binary_op(self, object other, void (*op)(mpq_t, mpq_srcptr, mpq_srcptr))
    cdef int _cmp(self, object other)
