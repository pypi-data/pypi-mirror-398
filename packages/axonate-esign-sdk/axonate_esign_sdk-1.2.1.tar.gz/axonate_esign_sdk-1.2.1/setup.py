"""
Axonate eSign SDK - Python SDK for Indian eSign (Digital Signature) Integration
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
try:
    long_description = (this_directory / "README.md").read_text(encoding='utf-8')
except FileNotFoundError:
    long_description = "Python SDK for Indian eSign (Digital Signature) Integration"

setup(
    name="axonate-esign-sdk",
    version="1.2.1",
    author="Axonate Tech",
    author_email="info@axonatetech.com",
    description="Python SDK for Indian eSign (Digital Signature) Integration - eSign API v2.1/v3.3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://axonatetech.com/",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Security :: Cryptography",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows",
    ],
    keywords="esign digital-signature india aadhaar pdf-signing cryptography axonate",
    python_requires=">=3.8",
    install_requires=[
        "pythonnet>=3.0.0",
        "lxml>=4.9.0",
        "cryptography>=41.0.0",
        "requests>=2.31.0",
    ],
    extras_require={
        "xml-signing": [
            "managex-xml-sdk>=1.0.0",
        ],
    },
    package_data={
        "esign_sdk": [
            "lib/native/*.dll",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    project_urls={
        "Homepage": "https://axonatetech.com/",
        "Support": "mailto:info@axonatetech.com",
    },
)
