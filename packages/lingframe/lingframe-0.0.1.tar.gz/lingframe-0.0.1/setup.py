from setuptools import setup, find_packages

long_description = "A placeholder package to reserve the name 'lingframe' on PyPI."

setup(
    name="lingframe",
    version="0.0.1",
    author="opensourcelater",
    author_email="opensourcelater@example.com",
    description="A placeholder package for lingframe",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/opensourcelater/lingframe",
    packages=find_packages(),
    license="Apache Software License",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
