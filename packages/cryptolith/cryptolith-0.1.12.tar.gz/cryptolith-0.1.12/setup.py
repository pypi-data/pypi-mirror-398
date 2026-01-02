from setuptools import setup, find_packages, Extension
import os
import sys

try:
    from Cython.Build import cythonize
    USE_CYTHON = True
except ImportError:
    USE_CYTHON = False

# Modules to be compiled into native binaries
COMPILED_MODULES = [
    "cryptolith.core",
    "cryptolith.obfuscator",
    "cryptolith.license_manager",
    "cryptolith.bcc_engine",
    "cryptolith.runtime",
    "cryptolith.virtualizer",
]

ext_modules = []
if USE_CYTHON:
    ext_modules = cythonize([
        Extension(mod, [f"src/{mod.replace('.', '/')}.py"])
        for mod in COMPILED_MODULES
    ], compiler_directives={'language_level': "3"})

# Custom build_py to exclude .py source for compiled modules
from setuptools.command.build_py import build_py as _build_py

class build_py(_build_py):
    def find_package_modules(self, package, package_dir):
        modules = super().find_package_modules(package, package_dir)
        return [
            (pkg, mod, file)
            for pkg, mod, file in modules
            if f"{pkg}.{mod}" not in COMPILED_MODULES
        ]

    def run(self):
        super().run()
        # Remove generated .c and .cpp files from the build directory
        # so they don't end up in the wheel
        if os.path.exists(self.build_lib):
            for root, dirs, files in os.walk(self.build_lib):
                for file in files:
                    if file.endswith(".c") or file.endswith(".cpp"):
                        try:
                            os.remove(os.path.join(root, file))
                        except OSError:
                            pass

setup(
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    ext_modules=ext_modules,
    cmdclass={'build_py': build_py} if USE_CYTHON else {},
)
