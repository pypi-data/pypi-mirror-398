from setuptools import setup, Extension
import pybind11

ext_modules = [
    Extension(
        "coolpy._mymath",
        sources=[
            "src/coolpy/_mymath.cpp",
            "src/coolpy/nelder_mead.cpp",
            "src/coolpy/rk4_beta.cpp",
        ],
        include_dirs=[pybind11.get_include()],
        language="c++",
        extra_compile_args=["-std=c++14"],
    )
]

setup(ext_modules=ext_modules)
