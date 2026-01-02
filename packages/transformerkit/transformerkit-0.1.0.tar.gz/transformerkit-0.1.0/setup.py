from setuptools import setup, find_packages
import os

# Read long description from README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
def read_requirements(filename):
    with open(filename, "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="transformerkit",
    version="0.1.0",
    author="Charan Sai Soma",
    author_email="contact@charansai.dev",  # Update with your actual email
    description="A complete implementation of the Transformer architecture in PyTorch",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/charansoma3001/transformerkit",
    project_urls={
        "Bug Tracker": "https://github.com/charansoma3001/transformerkit/issues",
        "Documentation": "https://github.com/charansoma3001/transformerkit#readme",
        "Source Code": "https://github.com/charansoma3001/transformerkit",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "torch>=2.0.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "isort>=5.12.0",
            "ipython>=8.14.0",
        ],
    },
    include_package_data=True,
)
