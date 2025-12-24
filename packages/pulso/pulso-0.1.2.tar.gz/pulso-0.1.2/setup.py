from setuptools import setup, find_packages
from pathlib import Path

# Read README.md with UTF-8 encoding
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="pulso",
    version="0.1.0",
    author="Juan Denis",
    author_email="juan@vene.co",
    description="Pulso delivers stateful web fetching with cache, hashes, and domain-aware rules",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jhd3197/Pulso",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "playwright>=1.40.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "api": [
            "flask>=2.3.0",
        ],
        "redis": [
            "redis>=5.0.0",
        ],
        "all": [
            "redis>=5.0.0",
            "flask>=2.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pulso=pulso.cli:main",
        ]
    },
)
