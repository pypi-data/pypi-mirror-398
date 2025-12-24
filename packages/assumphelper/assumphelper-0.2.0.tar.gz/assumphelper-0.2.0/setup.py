from setuptools import setup, find_packages
from pathlib import Path

# Read README.md safely with UTF-8
this_directory = Path(__file__).parent
readme_path = this_directory / "README.md"
long_description = readme_path.read_text(encoding="utf-8")  # <-- UTF-8 here

setup(
    name="assumphelper",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "scipy>=1.11.0",
        "statsmodels>=0.14.0",
        "scikit-learn>=1.3.0",
        "matplotlib>=3.8.0"
    ],
    python_requires=">=3.8",
    author="Aque, Badilla, Caaminio, Moog, Prollo",
    author_email="rodelpellazar1@gmail.com",
    description="Linear Regression Assumption Interpretation Guide",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rodelcoder1/OOP2",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
