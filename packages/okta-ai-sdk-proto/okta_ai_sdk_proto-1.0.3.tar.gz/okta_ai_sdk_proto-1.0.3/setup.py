#!/usr/bin/env python3
"""
Setup script for okta-ai-sdk-python
"""

from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="okta-ai-sdk-proto",
    version="1.0.3",
    author="Okta Inc.",
    author_email="developers@okta.com",
    description="Comprehensive Okta SDK for AI applications with Token Exchange, Cross-App Access (ID-JAG), and Connected Accounts support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/okta/okta-ai-sdk-proto",
    project_urls={
        "Bug Tracker": "https://github.com/okta/okta-ai-sdk-proto/issues",
        "Documentation": "https://github.com/okta/okta-ai-sdk-proto#readme",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
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
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Security",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "PyJWT>=2.6.0",
        "cryptography>=3.4.8",
        "pydantic>=1.10.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "mypy>=1.0.0",
            "flake8>=5.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "httpx>=0.24.0",
        ],
    },
    keywords=[
        "okta",
        "ai",
        "token-exchange",
        "cross-app-access",
        "id-jag",
        "oauth",
        "jwt",
        "authentication",
        "authorization",
        "langraph",
    ],
)

