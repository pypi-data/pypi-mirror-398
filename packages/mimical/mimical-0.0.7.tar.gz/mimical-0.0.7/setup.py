import setuptools
from setuptools import setup
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='mimical',

    version='0.0.7',

    description='Intesity modelling of multiply-imaged objects',

    long_description=long_description,

    long_description_content_type='text/markdown',

    author='Struan Stevenson',

    author_email='struan.stevenson@ed.ac.uk',

    packages= setuptools.find_packages(),

    package_data = {'': ['*.txt', '*.fits'],},  

    install_requires=["numpy", "astropy", "matplotlib", "nautilus-sampler", "petrofit"],

)