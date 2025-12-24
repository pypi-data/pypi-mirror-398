from setuptools import setup, find_packages

setup(
    name="voltops",
    version="0.2.0",
    author="Madhur Thareja",
    author_email="madhurthareja1105@gmail.com",
    description="A Python library for electronic formulas and signal processing",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/madhurthareja/voltops",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "scipy>=1.7.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)