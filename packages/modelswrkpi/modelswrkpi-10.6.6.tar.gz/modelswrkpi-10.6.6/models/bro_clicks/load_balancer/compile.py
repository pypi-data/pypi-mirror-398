from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
ext_modules = [
    Extension("v1",  ["v1.py"], extra_compile_args=["-g0"]),
    Extension("v2",  ["v2.py"], extra_compile_args=["-g0"]),
    Extension("v3",  ["v3.py"], extra_compile_args=["-g0"]),
    Extension("v4",  ["v4.py"], extra_compile_args=["-g0"]),
    Extension("v5",  ["v5.py"], extra_compile_args=["-g0"]),
    Extension("v6",  ["v6.py"], extra_compile_args=["-g0"]),
    Extension("v7",  ["v7.py"], extra_compile_args=["-g0"]),
]
setup(
    name='load_balancer',
    cmdclass={'build_ext': build_ext},
    ext_modules=ext_modules
)
