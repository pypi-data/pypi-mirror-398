from setuptools import setup, find_packages
from pathlib import Path

here = Path(__file__).parent

# Read README with UTF-8 (fixes Windows cp1252 decode issues)
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name='ncuhep',
    version='0.2.22',  # bump version for the new (non-MIT) license
    author='Phay Kah Seng',
    author_email='phay_ks@icloud.com',
    description='NCU High Energy Physics tools for muography and related analysis.',
    long_description=long_description,
    long_description_content_type='text/markdown',

    packages=find_packages(),
    include_package_data=True,
    package_data={
        "ncuhep.muography.muonscatter.predictors": ["*.npz"],
        "ncuhep.muography.demviewer.resources": ["data/*"],
    },

    # Custom restrictive license — make sure you have a LICENSE file in the repo
    license='NCUHEP Research License (see LICENSE)',
    license_files=['LICENSE'],

    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: Other/Proprietary License',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Physics',
    ],

    python_requires='>=3.11',

    install_requires=[
        'opencv-python',
        'numpy',
        'scipy',
        'iminuit',
        'matplotlib==3.9.4',
        'tqdm',
        'numba==0.62.0rc2',
        'pandas',
        'psutil',
        'PyQt6',
        'PyQt5',
        'daemonflux',
        'pyqtgraph',
        'PyOpenGL',
        'PyOpenGL-accelerate',
    ],
)
