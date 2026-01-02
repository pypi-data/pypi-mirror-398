from setuptools import setup, find_packages

setup(
    name="auto_clean",
    version="0.1.0",
    author="Jeet Dave",
    author_email="jd.878@njit.edu",
    description="AutoClean: Automated data cleaning library for pandas DataFrames",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/jd878-gif/autoclean",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.5",
        "numpy>=1.23"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)
