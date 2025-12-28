from setuptools import setup, find_packages

# Read the contents of your README file for the long description on PyPI
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="racket-lab",
    version="0.1.0",
    author="Liwaa Hosh",
    author_email="your.email@example.com",
    description="A Python library for tennis equipment physics and analytics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LiwaaCoder/racket-lab",
    
    # Configuration for 'src' layout
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    python_requires='>=3.7',
)
