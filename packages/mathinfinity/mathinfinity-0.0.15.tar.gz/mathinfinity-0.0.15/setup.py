from setuptools import setup, find_packages
from pathlib import Path
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Education",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Operating System :: OS Independent",
]
this_directory = Path(__file__).parent
long_description = (this_directory / "README.txt").read_text()

setup(
    name="mathinfinity",
    version='0.0.15',
    description="mathinfinity Python Package Is For All Types Of Mathematical Solutions.",
    url="",
    author="ATISH KUMAR SAHU",
    author_email="kumarsahuatishoff280301@gmail.com",
    license='MIT',
    license_files=("LICENSE",),
    classifiers=classifiers,
    keywords='mathinfinity, arithmetic operations, addition, subtraction, multiplication, division, modulo',
    packages=find_packages(),
    long_description=long_description,
    long_description_content_type="text/markdown", 
    install_requires=[],
)