from setuptools import setup, find_packages
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
setup(
        name='smolprintf',
        version='0.1.1',
        long_description=long_description,
        long_description_content_type='text/markdown',
        packages=find_packages(),
)
