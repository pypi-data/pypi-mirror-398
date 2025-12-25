"""
Setup file for publishing my_feature_package to PyPI
This is specifically for my_feature_package only
"""

from setuptools import setup, find_packages

# Read README for long description
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "Text formatting and validation utilities for Python"

setup(
    name="my-feature-package",  # ⚠️ CHANGE THIS to a unique name on PyPI!
    version="0.1.0",
    author="Your Name",  # ⚠️ CHANGE THIS to your name
    author_email="your.email@example.com",  # ⚠️ CHANGE THIS to your email
    description="Text formatting and validation utilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/my-feature-package",  # ⚠️ Optional: Change if you have a GitHub repo
    packages=find_packages(include=["my_feature_package", "my_feature_package.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
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
    keywords="text formatting, validation, text processing, utilities",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/my-feature-package/issues",
        "Source": "https://github.com/yourusername/my-feature-package",
    },
)

