from setuptools import setup, find_packages

setup(
    name="pygen-modules",
    version="1.0.1",
    packages=find_packages(),
    description="Generate CRUD and FormData boilerplate",
    author="Manikandan",
    python_requires=">=3.8",
    entry_points={"console_scripts": ["pygen=pygen_modules.installer:cli"]},
)
