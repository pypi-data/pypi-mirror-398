import os
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fiber-uploader",
    version="1.2.1",
    description="A lightweight, zero-dependency PyPI uploader.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Eternals",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "fiber=fiber.core:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

