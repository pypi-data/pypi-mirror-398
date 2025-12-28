"""
Setup script for Backboard Python SDK
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="backboard-sdk",
    version="1.4.4",
    author="Backboard",
    author_email="support@backboard.io",
    description="Python SDK for the Backboard API - Build conversational AI applications with persistent memory and intelligent document processing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/backboard/backboard-python-sdk",
    packages=find_packages(),
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
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "httpx>=0.27.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
        "mypy>=1.0.0",
        "types-httpx",
        ],
    },
    keywords="ai, api, sdk, conversational, chatbot, assistant, documents, rag",
    project_urls={
        "Bug Reports": "https://github.com/backboard/backboard-python-sdk/issues",
        "Source": "https://github.com/backboard/backboard-python-sdk",
        "Documentation": "https://app.backboard.io/docs",
    },
)
