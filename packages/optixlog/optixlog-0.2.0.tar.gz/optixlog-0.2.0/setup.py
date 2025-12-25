from setuptools import setup, find_packages

setup(
    name='optixlog',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'requests',
        'numpy',
        'matplotlib',
        'pillow',
        'rich>=13.0.0',
        'click>=8.0.0',
        'tomli>=2.0.0;python_version<"3.11"',
    ],
    extras_require={
        'mpi': ['mpi4py'],
        'meep': ['meep'],
    },
    entry_points={
        'console_scripts': [
            'optixlog=optixlog.cli.main:main',
            'ox=optixlog.cli.main:main',
        ],
    },
)