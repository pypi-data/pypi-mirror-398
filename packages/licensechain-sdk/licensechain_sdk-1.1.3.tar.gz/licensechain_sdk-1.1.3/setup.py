#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from setuptools import find_packages, setup

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if not os.path.exists(requirements_path):
        # Fallback to default requirements if file not found
        return [
            "httpx>=0.24.0",
            "pydantic>=2.0.0",
            "typing-extensions>=4.5.0",
        ]
    with open(requirements_path, "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="licensechain-sdk",
    version="1.1.3",
    author="LicenseChain",
    author_email="support@licensechain.app",
    description="Official LicenseChain Python SDK for license management and validation",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/LicenseChain/LicenseChain-Python-SDK",
    project_urls={
        "Bug Reports": "https://github.com/LicenseChain/LicenseChain-Python-SDK/issues",
        "Source": "https://github.com/LicenseChain/LicenseChain-Python-SDK",
        "Documentation": "https://docs.licensechain.app/sdks/python",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Security",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "httpx>=0.24.0",
        ],
    },
    keywords="license, validation, api, sdk, python, licensechain",
    include_package_data=True,
    zip_safe=False,
)
