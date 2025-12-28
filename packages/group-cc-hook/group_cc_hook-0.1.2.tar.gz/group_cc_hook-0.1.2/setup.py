# setup.py
import os

from setuptools import setup, find_packages


# Read README as long description
def read_long_description():
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""


setup(
    name="group_cc_hook",
    version="0.1.2",
    description="A hook for torch.distributed ProcessGroup primitives with timeout detection",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    author="Yang Rudan",
    url="https://github.com/yangrudan/group_cc_hook",
    # Version requirements
    python_requires=">=3.7,<3.13",
    # Python packages
    packages=find_packages(exclude=["tests", "tests.*", "doc"]),
    # Dependency declaration
    install_requires=[
        "torch>=1.8.0,<3.0.0",  # Explicit PyTorch version range
    ],
    # PyPI classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: System :: Monitoring",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
        "Operating System :: POSIX :: Linux",
    ],
    # Keywords
    keywords="pytorch distributed monitoring timeout hook nccl",
)
