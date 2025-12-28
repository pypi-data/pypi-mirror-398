"""Setup configuration for mlleak package."""
from setuptools import setup, find_packages

setup(
    name="mlleak",
    version="0.1.0",
    description="ML Data Leakage & Split Sanity Checker - Detect duplicates, time leakage, and group leakage in train/test splits",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Thirumurugan",
    author_email="thirumuruganchandru01@gmail.com",
    url="https://github.com/thirumurugan/mlleak",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.0.0",
        "numpy>=1.18.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Quality Assurance",
    ],
    python_requires='>=3.8',
    license="MIT",
    include_package_data=True,
    keywords=["machine-learning", "data-leakage", "train-test-split", "data-science", "ml-validation"],
)
