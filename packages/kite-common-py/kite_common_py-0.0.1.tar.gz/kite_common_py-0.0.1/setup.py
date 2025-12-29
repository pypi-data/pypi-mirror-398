"""
Setup script for kite-common package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="kite-common-py",
    version="0.1.0",
    author="Addy",
    author_email="adityag7077@gmail.com",
    description="Kite Common Python Package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kite/kite-common-py",
    project_urls={
        "Bug Tracker": "https://github.com/kite/kite-common-py/issues",
        "Source Code": "https://github.com/kite/kite-common-py",
    },
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
        "Framework :: Django",
        "Framework :: Flask",
        "Framework :: FastAPI",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    keywords="countries currencies timezones languages error-codes common-data",
    include_package_data=True,
    package_data={
        "kite_common": ["data/*.json"],
    },
    zip_safe=False,
)
