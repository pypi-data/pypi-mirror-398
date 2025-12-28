"""Setup script for Crexperium Python SDK."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="crexperium",
    version="1.0.5",
    author="Crexperium Team",
    author_email="support@crexperium.com",
    description="Official Python SDK for Crexperium CRM API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/crexperium/crexperium-python-sdk",
    packages=find_packages(exclude=["tests", "tests.*", "examples"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
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
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
    },
    keywords="crm api sdk crexperium",
    project_urls={
        "Bug Reports": "https://github.com/crexperium/crexperium-python-sdk/issues",
        "Source": "https://github.com/crexperium/crexperium-python-sdk",
        "Documentation": "https://docs.crexperium.com",
    },
)
