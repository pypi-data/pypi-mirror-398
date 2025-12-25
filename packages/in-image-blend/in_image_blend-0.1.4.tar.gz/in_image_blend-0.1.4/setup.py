# setup.py
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
import numpy

try:
    from Cython.Build import cythonize
    use_cython = True
except ImportError:
    use_cython = False
    
    
ext = ".pyx" if use_cython else ".c"
extensions = [
    Extension(
        "in_image_blend.image_blend", 
        ["in_image_blend/image_blend"+ ext],  
        include_dirs=[numpy.get_include()],
        define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
    )
]

if use_cython:
    extensions = cythonize(extensions, compiler_directives={"language_level": "3"})

class INBuildExt(build_ext):
    def finalize_options(self):
        build_ext.finalize_options(self)
        import numpy
        self.include_dirs.append(numpy.get_include())
        
setup(
    name="in_image_blend",
    version="0.1.4",
    author="in_xs",
    packages=find_packages(),
    ext_modules=extensions,
    cmdclass={"build_ext": INBuildExt},
    install_requires=["numpy", "Cython"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Cython",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
