"""Setup configuration for Dremio CLI."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dremio-cli",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A comprehensive CLI for Dremio Cloud and Dremio Software",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/dremio-cli",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "click>=8.1.0",
        "requests>=2.31.0",
        "pyyaml>=6.0",
        "rich>=13.0.0",
        "python-dateutil>=2.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "isort>=5.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "dremio=dremio_cli.cli:main",
        ],
    },
)
