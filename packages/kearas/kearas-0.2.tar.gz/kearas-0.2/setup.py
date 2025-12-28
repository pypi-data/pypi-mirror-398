from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of your README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text() #Gets the long description from Readme file

setup(
    name='kearas',
    version='0.2',
    packages=find_packages(),
    install_requires=[
        'pandas',
    ],  # Add a comma here
    description='This is the short description',

    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    
)