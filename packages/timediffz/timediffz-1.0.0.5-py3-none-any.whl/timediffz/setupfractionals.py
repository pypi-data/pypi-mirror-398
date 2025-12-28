from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        name="fractionals",
        sources=["fractionals.pyx"],
        language="c++",
        libraries=["gmp"],  # link against GMP
        extra_compile_args=["-std=c++17"],  # optional, C++ standard
    )
]

setup(
    name="Fraction",
    ext_modules=cythonize(extensions, compiler_directives={"language_level": "3"}),
)
