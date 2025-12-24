from setuptools import setup, find_packages
import os

# This handles the missing README by providing a fallback description
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "Python SDK for DistributeX distributed computing platform"

setup(
    name="distributex-cloud",
    version="8.0.3",
    author="DistributeX Team",
    author_email="N/A",
    description="Python SDK for DistributeX distributed computing platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DistributeX-Cloud/distributex",
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
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
    ],
    keywords="distributed computing cloud serverless api",
    project_urls={
        "Bug Reports": "https://github.com/DistributeX-Cloud/distributex/issues",
        "Documentation": "https://docs.distributex.cloud",
        "Source": "https://github.com/DistributeX-Cloud/distributex",
    },
)
