from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

# Get the numpy include directory
numpy_include = np.get_include()

# Define extensions - Cython will compile .py files
extensions = [
    Extension(
        "image_thr.main",
        ["src/image_thr/main.py"],
        include_dirs=[numpy_include],
    ),
]

# Cython compiler directives for optimization
compiler_directives = {
    'language_level': "3",
    'boundscheck': False,  # Disable bounds checking for speed
    'wraparound': False,   # Disable negative indexing for speed
    'initializedcheck': False,  # Disable checks for uninitialized variables
    'cdivision': True,     # Use C-style division
    'nonecheck': False,    # Disable None checks
    'optimize.use_switch': True,  # Optimize if/elif chains
    'optimize.unpack_method_calls': True,  # Optimize method calls
}

setup(
    ext_modules=cythonize(
        extensions,
        compiler_directives=compiler_directives,
        build_dir="build",
    ),
    zip_safe=False,
)

