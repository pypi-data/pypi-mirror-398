"""
Setup file for publishing text formatting and validation package to PyPI
"""

from setuptools import setup, find_packages

# Read README for long description
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "Professional text formatting and validation utilities for Python developers"

setup(
    name="textformatter-plus",  # ⚠️ CHANGE THIS to your desired package name (check availability on PyPI first!)
    version="1.0.1",  # ⚠️ Update version for each release (incremented because 1.0.0 was deleted)
    author="Your Company Name",  # ⚠️ CHANGE THIS
    author_email="your.email@example.com",  # ⚠️ CHANGE THIS
    description="Professional text formatting and validation utilities for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/textformatter-plus",  # ⚠️ Optional: Change if you have a GitHub repo
    packages=find_packages(include=["my_feature_package", "my_feature_package.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.8",
    install_requires=[],  # Add dependencies here if needed
    keywords="text formatting, validation, text processing, utilities, professional, text manipulation",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/textformatter-plus/issues",
        "Source": "https://github.com/yourusername/textformatter-plus",
        "Documentation": "https://github.com/yourusername/textformatter-plus#readme",
    },
)
