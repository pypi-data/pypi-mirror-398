from setuptools import setup, find_packages
from pathlib import Path


def get_version():
    version = {}
    with open("wp21_train/utils/version.py") as f:
        exec(f.read(), version)
    return version["__version__"]


README = Path(__file__).with_name("README.md")
long_description = README.read_text(encoding="utf-8") if README.exists() else ""

setup(
    name="wp21_train",
    version=get_version(),
    author="ATLAS NextGen WP2.1",
    author_email="ngtwp21@cern.ch",
    description=(
        "Framework that provides tools allowing for monitoring, training and evaluating ML models"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.cern.ch/atlas-nextgen-wp21/wp21_training_framework.git",
    packages=find_packages(exclude=("tests", "docs")),
    include_package_data=True,
    package_data={
        "wp21_train.physics.clustering.backends": ["*.cpp", "*.h"],
    },
    python_requires=">=3.10",
    install_requires=[
        "numpy>=1.21,<2.0",
        "PyYAML>=6.0,<7.0",
        "uproot>=5.0,<6.0",
        "awkward>=2.5,<3.0",
        "lz4>=4.3,<5.0",
        "xxhash>=3.4,<4.0",
        "tqdm>=4.67.1",
        "pybind11>=3.0.1",
        "vector>=1.7.0",
        "pyarrow>=18.0.0",
        "hgq==0.2.6",
    ],
    extras_require={
        "torch": ["torch>=2.1"],
        "tensorflow": ["tensorflow>=2.13"],
        "tf-tools": ["tf2onnx>=1.14"],
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "ruff>=0.4",
            "mypy>=1.5",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
