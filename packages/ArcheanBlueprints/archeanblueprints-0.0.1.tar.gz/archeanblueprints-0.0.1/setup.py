from setuptools import setup, find_packages

long_description = None
with open("README.md", "r") as file:
    long_description = file.read()

setup(
    name='ArcheanBlueprints',
    version='0.0.1',
    description="A library for extracting and optimizing Archean blueprints.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    url="https://github.com/Marlo3110/ArcheanBlueprints",
    install_requires=[
        # 'some_dependency>=1.0.0',
    ],
    extras_require={
        "dev": ["twine>=4.0.2"]
    }
)