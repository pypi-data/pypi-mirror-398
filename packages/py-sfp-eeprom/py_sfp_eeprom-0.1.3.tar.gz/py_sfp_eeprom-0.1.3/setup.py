"""Setup configuration for py-sfp-eeprom package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="py-sfp-eeprom",
    version="0.1.3",
    author="py-sfp-eeprom contributors",
    description="Python library for creating and manipulating SFP EEPROM data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Better-Internet-Ltd/py-sfp-eeprom",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Telecommunications Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Hardware",
        "Operating System :: OS Independent",
    ],
    keywords="sfp eeprom fiber optics transceiver sff-8472",
    python_requires=">=3.7",
    license="MIT",
)
