"""Setup configuration for arcpaykit Python package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="arcpaykit",
    version="0.2.0",
    description="Official ArcPay Python SDK for accepting stablecoin payments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ArcPay",
    author_email="support@arcpaykit.com",
    url="https://github.com/arcpay/gateway",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial",
    ],
    keywords="payments, web3, stablecoin, arcpay, blockchain, cryptocurrency",
    project_urls={
        "Documentation": "https://docs.arcpaykit.com",
        "Source": "https://github.com/arcpay/gateway",
        "Tracker": "https://github.com/arcpay/gateway/issues",
    },
)

