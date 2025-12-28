# fractionals.pyx
# distutils: language=c++
# cython: language_level=3

from decimal import Decimal, localcontext
from fractionals cimport *

cdef class Fraction:

    def __cinit__(self):
        mpq_init(self.value)

    def __dealloc__(self):
        mpq_clear(self.value)

    # -----------------------
    # Helper: set fraction from Python ints (arbitrary size)
    # -----------------------
    cdef void _set_from_bigints(self, object num, object den):
        cdef mpz_t num_mpz, den_mpz
        mpz_init(num_mpz)
        mpz_init(den_mpz)
        mpz_set_str(num_mpz, str(num).encode(), 10)
        mpz_set_str(den_mpz, str(den).encode(), 10)
        mpq_set_num(self.value, num_mpz)
        mpq_set_den(self.value, den_mpz)
        mpq_canonicalize(self.value)
        mpz_clear(num_mpz)
        mpz_clear(den_mpz)

    # -----------------------
    # Initialize from Python object
    # -----------------------
    cdef void _set_from_object(self, object a):
        cdef Fraction bf

        if isinstance(a, int):
            self._set_from_bigints(a, 1)

        elif isinstance(a, float):
            s = format(a, ".50g")
            mpq_set_str(self.value, s.encode(), 10)
            mpq_canonicalize(self.value)

        elif isinstance(a, Decimal):
            try:
                numerator, denominator = a.as_integer_ratio()
                self._set_from_bigints(numerator, denominator)
            except OverflowError:
                s = format(a, "f")
                if '.' in s:
                    integer_part, frac_part = s.split('.')
                    numerator_str = integer_part + frac_part
                    denominator_str = '1' + '0' * len(frac_part)
                else:
                    numerator_str = s
                    denominator_str = '1'
                self._set_from_bigints(numerator_str, denominator_str)

        elif isinstance(a, str):
            if '/' in a:
                parts = a.split('/')
                if len(parts) != 2:
                    raise ValueError(f"Invalid fraction string: {a}")
                self._set_from_bigints(parts[0].strip(), parts[1].strip())
            else:
                mpq_set_str(self.value, a.encode(), 10)
                mpq_canonicalize(self.value)

        elif isinstance(a, Fraction):
            bf = <Fraction>a
            mpq_set(self.value, bf.value)

        else:
            raise TypeError(f"Cannot convert type {type(a)} to Fraction")

    # -----------------------
    # Constructor
    # -----------------------
    def __init__(self, *args):
        if len(args) == 0:
            mpq_set_si(self.value, 0, 1)
        elif len(args) == 1:
            self._set_from_object(args[0])
        elif len(args) == 2:
            num, den = args
            if den == 0:
                raise ZeroDivisionError("Denominator cannot be zero")
            self._set_from_bigints(num, den)
        else:
            raise TypeError("Fraction() takes 0, 1, or 2 arguments")

    # -----------------------
    # Arithmetic helpers
    # -----------------------
    cdef Fraction _binary_op(self, object other,
                             void (*op)(mpq_t, mpq_srcptr, mpq_srcptr)):
        cdef Fraction result = Fraction()
        cdef Fraction o
        if isinstance(other, Fraction):
            o = <Fraction>other
        else:
            o = Fraction(other)
        op(result.value, self.value, o.value)
        return result

    def __add__(self, other): return self._binary_op(other, mpq_add)
    def __sub__(self, other): return self._binary_op(other, mpq_sub)
    def __mul__(self, other): return self._binary_op(other, mpq_mul)
    def __truediv__(self, other): return self._binary_op(other, mpq_div)

    def __radd__(self, other): return Fraction(other) + self
    def __rsub__(self, other): return Fraction(other) - self
    def __rmul__(self, other): return Fraction(other) * self
    def __rtruediv__(self, other): return Fraction(other) / self

    # -----------------------
    # Comparisons
    # -----------------------
    cdef int _cmp(self, object other):
        cdef Fraction o
        if isinstance(other, Fraction):
            o = <Fraction>other
        else:
            o = Fraction(other)
        return mpq_cmp(self.value, o.value)

    def __eq__(self, other): return self._cmp(other) == 0
    def __ne__(self, other): return self._cmp(other) != 0
    def __lt__(self, other): return self._cmp(other) < 0
    def __le__(self, other): return self._cmp(other) <= 0
    def __gt__(self, other): return self._cmp(other) > 0
    def __ge__(self, other): return self._cmp(other) >= 0

    # -----------------------
    # String / representation
    # -----------------------
    def __str__(self):
        cdef char* s = mpq_get_str(NULL, 10, self.value)
        py_str = s.decode()
        free(s)
        return py_str

    def __repr__(self):
        return f"Fraction('{str(self)}')"

    # -----------------------
    # Numerator / Denominator
    # -----------------------
    @property
    def numerator(self):
        cdef mpz_ptr num = mpq_numref(self.value)
        cdef char* s = mpz_get_str(NULL, 10, num)
        py_str = s.decode()
        free(s)
        return int(py_str)

    @property
    def denominator(self):
        cdef mpz_ptr den = mpq_denref(self.value)
        cdef char* s = mpz_get_str(NULL, 10, den)
        py_str = s.decode()
        free(s)
        return int(py_str)

    # -----------------------
    # Conversion
    # -----------------------
    def __float__(self):
        return self.numerator / self.denominator

    def __int__(self):
        return self.numerator // self.denominator

    def __round__(self, n=0):
        return round(float(self), n)

    def __trunc__(self):
        return self.numerator // self.denominator

    def as_integer_ratio(self):
        return (self.numerator, self.denominator)

    def __bool__(self):
        return self.numerator != 0

    def __hash__(self):
        return hash((self.numerator, self.denominator))

    def to_decimal(self, precision=None):
        if precision is None:
            return Decimal(self.numerator) / Decimal(self.denominator)
        else:
            with localcontext() as ctx:
                ctx.prec = precision
                return Decimal(self.numerator) / Decimal(self.denominator)
