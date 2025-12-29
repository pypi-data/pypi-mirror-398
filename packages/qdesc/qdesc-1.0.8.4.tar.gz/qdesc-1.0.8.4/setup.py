from setuptools import setup, find_packages 
from pathlib import Path 

# Read the contents of the README file 
this_directory = Path(__file__).parent 
long_description = (this_directory / "README.md").read_text()

setup(
    name='qdesc',
    version='1.0.8.4',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
        'scipy',
        'seaborn',
        'matplotlib',
        'statsmodels'
    ],
    author='Paolo Hilado',
    author_email='datasciencepgh@proton.me',
    description= 'Quick and Easy way to do descriptive analysis.',
    long_description=long_description, 
    long_description_content_type='text/markdown', # or 'text/x-rst' for reStructuredText # other metadata fields... )
)
