from pathlib import Path

import setuptools

VERSION = "0.0.7"

NAME = "hvala"

INSTALL_REQUIRES = [
    "numpy>=2.2.1",
    "scipy>=1.15.0",
    "networkx[default]>=3.4.2"
]

setuptools.setup(
    name=NAME,
    version=VERSION,
    description="Compute the Approximate Vertex Cover for undirected graph encoded in DIMACS format.",
    url="https://github.com/frankvegadelgado/hvala",
    project_urls={
        "Source Code": "https://github.com/frankvegadelgado/hvala",
        "Documentation Research": "https://dev.to/frank_vega_987689489099bf/the-hvala-algorithm-5395",
    },
    author="Frank Vega",
    author_email="vega.frank@gmail.com",
    license="MIT License",
    classifiers=[
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
    ],
    python_requires=">=3.12",
    # Requirements
    install_requires=INSTALL_REQUIRES,
    packages=["hvala"],
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    entry_points={
        'console_scripts': [
            'idemo = hvala.app:main',
            'test_idemo = hvala.test:main',
            'batch_idemo = hvala.batch:main'
        ]
    }
)