"""
Setup script for XMLCV
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

# Read version
version_file = Path(__file__).parent / "xmlcv" / "__init__.py"
version = "0.1.0"
if version_file.exists():
    for line in version_file.read_text().splitlines():
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"').strip("'")
            break

setup(
    name="xmlcv",
    version=version,
    author="Trung Hia Hoang",
    author_email="trunghia.hoang@gmail.com",
    description="A flexible XML to document converter with dynamic element processing and plugin system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/trunghiahoang/xmlcv",
    project_urls={
        "Homepage": "https://github.com/trunghiahoang/xmlcv",
        "Documentation": "https://github.com/trunghiahoang/xmlcv#readme",
        "Repository": "https://github.com/trunghiahoang/xmlcv",
        "Bug Tracker": "https://github.com/trunghiahoang/xmlcv/issues",
        "Changelog": "https://github.com/trunghiahoang/xmlcv/blob/main/CHANGELOG.md",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Text Processing :: Markup :: XML",
        "Topic :: Text Processing :: Markup :: HTML",
    ],
    python_requires=">=3.8",
    install_requires=[
        "lxml>=4.9.0",
    ],
    extras_require={
        "pdf": [
            "weasyprint>=59.0",
        ],
        "pdfkit": [
            "pdfkit>=1.0.0",
        ],
        "docx": [
            "python-docx>=1.0.0",
        ],
        "pptx": [
            "python-pptx>=0.6.0",
        ],
        "markdown": [
            "markdown>=3.4.0",
        ],
        "all": [
            "weasyprint>=59.0",
            "python-docx>=1.0.0",
            "python-pptx>=0.6.0",
            "markdown>=3.4.0",
        ],
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "xmlcv=xmlcv.cli:main",
        ],
    },
)

