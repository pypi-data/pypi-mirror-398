from setuptools import setup, find_packages


with open("PyPIREADME.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='melissadatacloudapi',
    version='3.14.000', #change in the readme badges too
    packages=find_packages(where='.'),
    install_requires=[],  # List any dependencies here
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MelissaData/MelissaCloudAPI-Python3",

    include_package_data=True,
)
