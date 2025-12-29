"""
InvoiceAI Python SDK Setup
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="invoiceai",
    version="1.0.0",
    author="InvoiceAI",
    author_email="support@invoiceai.co.za",
    description="Official Python SDK for the InvoiceAI API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://invoiceai.co.za/api-docs",
    project_urls={
        "Documentation": "https://invoiceai.co.za/api-docs",
        "Support": "https://invoiceai.co.za/contact",
    },
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
        "Topic :: Office/Business :: Financial :: Accounting",
    ],
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
    ],
    extras_require={
        "async": ["aiohttp>=3.8.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },
    keywords=[
        "invoiceai",
        "invoice",
        "api",
        "sdk",
        "south-africa",
        "billing",
        "quotes",
        "clients",
    ],
)
