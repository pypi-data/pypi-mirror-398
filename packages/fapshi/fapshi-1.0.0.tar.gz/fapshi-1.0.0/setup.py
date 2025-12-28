"""Setup configuration for the Fapshi Python SDK."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="fapshi",
    version="1.0.0",
    description="Python SDK for the Fapshi Payment API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Fapshi",
    author_email="signeeric9@gmail.com",
    url="https://github.com/Fapshi/python-sdk",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.0.0",
            "black>=21.0.0",
            "flake8>=3.8.0",
            "mypy>=0.800",
        ],
    },
    project_urls={
       "Documentation": "https://docs.fapshi.com/en/api-reference/getting-started",
       "Homepage": "https://fapshi.com",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="fapshi payment api sdk",
)

