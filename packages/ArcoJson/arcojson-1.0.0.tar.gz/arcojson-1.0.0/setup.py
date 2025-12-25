"""Setup configuration for jsonutils."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="ArcoJson",
    version="1.0.0",
    author="Manu c",
    author_email="manuachu0611@gmail.com",
    description="A professional JSON to CSV conversion library with advanced features",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Manuachu06/PythonCustomePackage",
    packages=find_packages(exclude=["tests", "examples", "docs"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Filters",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Typing :: Typed",
    ],
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "sphinx>=6.0.0",
        ],
    },
    package_data={
        "ArcoJson": ["py.typed"],
    },
    keywords="json csv converter data conversion flatten nested",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/json2csv-pro/issues",
        "Source": "https://github.com/yourusername/json2csv-pro",
        "Documentation": "https://json2csv-pro.readthedocs.io",
    },
)