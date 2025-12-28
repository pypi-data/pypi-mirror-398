#from setuptools import setup
#
#with open("README.md", "r") as fh:
#    long_description = fh.read()
#
#setup(
#    name='coolpy',
#    version='0.0.64',
#    description='Muon ionization simulation program',
#    py_modules=["quadrupole"],
#    package_dir={'': 'src'},
#    classifiers =[
#        "Natural Language :: English",
#        "Programming Language :: Python :: 3.6",
#        "Programming Language :: Python :: 3.7",
#        "Programming Language :: Python :: 3.9",
#        "Programming Language :: Python :: 3.10",
#        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
#        "Operating System :: OS Independent",
#        #"Operating System :: iOS",
#        "Operating System :: MacOS",
#        "Operating System :: POSIX :: Linux",
#
#    ],
#    long_description=long_description,
#    long_description_content_type="text/markdown",
#
##    install_requires = [
##        "blessings ~= 1.7",
##        'numpy',
##        'matplotlib',
##        'scipy',
##        'shapely',
##    ],
#
##    extras_require = {
##        "dev": [
##            "pytest>=3.7",
##        ],
##      },
#
#    url = "https://github.com/BerndStechauner/coolpy",
#    author = "Bernd Stechauner",
#    author_email = "bernd.stechauner@cern.ch",
#)
#
#
## setup.py
#from setuptools import setup
#from pybind11.setup_helpers import Pybind11Extension, build_ext
#
#ext_modules = [
#    Pybind11Extension(
#        "coolpy._mymath",
#        ["src/coolpy/_mymath.cpp"],
#        cxx_std=17,  # macOS clang is happy with C++17
#    )
#]
#
#setup(
#    # keep your existing metadata/args here...
#    cmdclass={"build_ext": build_ext},
#    ext_modules=ext_modules,
#)

#from setuptools import setup
#from pybind11.setup_helpers import Pybind11Extension, build_ext
#
#ext_modules = [
#    Pybind11Extension(
#        "coolpy._mymath",
#        ["src/coolpy/_mymath.cpp"],
#        cxx_std=17,
#    )
#]
#
#setup(
#    cmdclass={"build_ext": build_ext},
#    ext_modules=ext_modules,
#)

#from setuptools import setup, find_packages
#from pybind11.setup_helpers import Pybind11Extension, build_ext
#
#ext_modules = [
#    Pybind11Extension(
#        "coolpy._mymath",
#        sources=[
#            "src/coolpy/_mymath.cpp",
#            "src/coolpy/rk4_beta.cpp",
#            "src/coolpy/nelder_mead.cpp",
#        ],
#        cxx_std=17,
#        extra_compile_args=["-O3", "-ffast-math"],
#    )
#]
#
#setup(
#    packages=find_packages(where="src"),
#    package_dir={"": "src"},
#    ext_modules=ext_modules,
#    cmdclass={"build_ext": build_ext},
#    zip_safe=False,
#)

from setuptools import setup



setup()
