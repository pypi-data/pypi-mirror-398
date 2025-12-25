"""Setup configuration for edutools-github-classroom package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="edutools-github-classroom",
    version="0.1.0",
    author="NajaSoft",
    author_email="contact@najasoft.com",
    description="A Python library for interacting with the GitHub Classroom REST API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/najasoft/edutools-github-classroom",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Education",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.28.0",
    ],
    keywords="github classroom education api teaching grading",
    project_urls={
        "Bug Reports": "https://github.com/najasoft/edutools-github-classroom/issues",
        "Source": "https://github.com/najasoft/edutools-github-classroom",
        "Documentation": "https://github.com/najasoft/edutools-github-classroom#readme",
    },
)
