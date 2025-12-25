from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tpm-fingerprint-lib",
    version="1.0.0",
    author="TPM Fingerprint Library",
    author_email="your.email@example.com",
    description="Comprehensive TPM-based device fingerprinting with cryptographically enforced governance",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/tpm-fingerprint-lib",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Security :: Cryptography",
        "Topic :: System :: Hardware",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.8",
    install_requires=[
        "cryptography>=41.0.0",
        "pywin32>=305; sys_platform == 'win32'",
        "WMI>=1.5.1; sys_platform == 'win32'",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "mypy>=1.5.0",
            "pylint>=2.17.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
        "enhanced": [
            # Uncomment when available
            # "devicefingerprintingpro>=1.0.0",
        ],
        "pqc": [
            # Uncomment when available
            # "pqcdualusb>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "tpm-fingerprint=tpm_fingerprint_lib.cli:main",
        ],
    },
    keywords="tpm fingerprint security attestation hardware cryptography policy enforcement",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/tpm-fingerprint-lib/issues",
        "Source": "https://github.com/yourusername/tpm-fingerprint-lib",
        "Documentation": "https://tpm-fingerprint-lib.readthedocs.io/",
    },
)
