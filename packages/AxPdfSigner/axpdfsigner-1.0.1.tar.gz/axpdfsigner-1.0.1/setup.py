from setuptools import setup, find_packages
import os

# Read README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read version
version = {}
with open("AxPdfSigner/__init__.py", "r") as f:
    for line in f:
        if line.startswith("__version__"):
            exec(line, version)

setup(
    name="AxPdfSigner",
    version=version.get("__version__", "1.0.0"),
    author="Axonate Tech",
    author_email="support@axonatetech.com",
    description="Professional PDF Digital Signature SDK - Pure Python Implementation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://axonatetech.com/",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business",
        "Topic :: Security :: Cryptography",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pythonnet>=3.0.0",
    ],
    package_data={
        "AxPdfSigner": [
            "_lib/*.dll",
            "_lib/*.pyd",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    license="Commercial",
    keywords="pdf signature digital-signature signing certificate pfx python",
    project_urls={
        "Homepage": "https://axonatetech.com/",
        "Documentation": "https://axonatetech.com/docs",
        "Support": "https://axonatetech.com/support",
    },
)
