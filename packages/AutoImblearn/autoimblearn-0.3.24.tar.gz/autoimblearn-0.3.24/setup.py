"""
AutoImblearn

The automated machine learning system for imbalanced data
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='AutoImblearn',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version="0.3.24",  # Add unsupervised learning + hyperparameter optimization

    description='Automated machine learning system for imbalanced medical data with survival analysis, unsupervised learning, and hyperparameter optimization',
    long_description=long_description,
    long_description_content_type="text/markdown",

    # The project's main homepage.
    # url='https://github.com/Wanghongkua/Auto-Imblearn2',

    # Author details
    author='Hank Wang',
    author_email='hankwang1991@gmail.com',

    # Choose your license
    license='BSD 3-Clause License',

    # Python Versions
    python_requires=">=3.9",

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],

    # What does your project relate to?
    keywords=['medical analysis','automated machine learning'],

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #   py_modules=["my_module"],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        "docker",
        "joblib",
        "pandas",
        "scikit-learn",
        "pydantic",
        "gensim",
        "flask",
        "optuna>=3.0.0",  # Hyperparameter optimization
    ],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]

    extras_require={
        "web": [
            "matplotlib",
            "seaborn",
        ],
        "imputer": [
            "hyperimpute",  # installed only when requested
        ],
        "resampler": [
            "smote_variants",
            "imbalanced-learn",
        ],
        "survival": [
            "scikit-survival>=0.22.0",  # survival analysis support
        ],
        "unsupervised": [
            "umap-learn",  # UMAP dimensionality reduction
        ],
        "r_model": [
            "rpy2",
        ],
        'dev': [
            'check-manifest',
        ],
    },

)
