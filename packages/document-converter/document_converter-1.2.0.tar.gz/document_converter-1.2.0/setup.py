"""
Document Converter - Setup Script

A comprehensive document conversion library with batch processing,
intelligent caching, and template rendering capabilities.
"""
from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
def read_requirements(path):
    reqs = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("#"):
                continue
            # ignore pip options / editable installs / file includes
            if line.startswith(("-e ", "-e", "--", "-r ", "-r")):
                continue
            reqs.append(line)
    return reqs

requirements = read_requirements("requirements.txt")
dev_requirements = read_requirements("requirements-dev.txt")

setup(
    name="document-converter",
    version="1.2.0",
    author="Document Converter Team",
    author_email="dev@example.com",
    description="Comprehensive document conversion library with batch processing, caching, and template rendering",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MikeAMSDev/document-converter",
    project_urls={
        "Bug Tracker": "https://github.com/MikeAMSDev/document-converter/issues",
        "Source Code": "https://github.com/MikeAMSDev/document-converter",
        "Changelog": "https://github.com/MikeAMSDev/document-converter/blob/main/CHANGELOG.md",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: General",
        "Topic :: Office/Business",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=2.0.0",
            "m2r2>=0.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "document-converter=cli.main:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.md"],
    },
    keywords=[
        "document", "conversion", "pdf", "docx", "html", "markdown",
        "batch", "processing", "caching", "template", "rendering"
    ],
    zip_safe=False,
)
