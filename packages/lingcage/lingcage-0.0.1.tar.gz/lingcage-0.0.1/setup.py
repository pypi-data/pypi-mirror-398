from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lingcage",
    version="0.0.1",
    author="opensourcelater",
    author_email="opensourcelater@example.com",
    description="A placeholder package for lingcage",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/opensourcelater/lingcage",
    packages=find_packages(),
    license="Apache Software License",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
