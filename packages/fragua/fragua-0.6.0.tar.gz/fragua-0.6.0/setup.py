"""Setup file."""

from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="fragua",
    version="0.6.0",
    author="SagoDev",
    description="Package for creating ETL environments for data analysis",
    packages=find_packages(where=".", include=["fragua", "fragua.*"]),
    include_package_data=True,
    package_data={"fragua": ["py.typed"]},
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.10",
    url="https://github.com/SagoDev/Fragua",
    install_requires=[
        "numpy",
        "pandas",
        "pytest",
        "sqlalchemy",
        "requests",
        "scikit-learn",
        "typing_extensions",
    ],
)
