from setuptools import setup, find_packages
import os

setup(
    name="PyBrKarma",
    version="1.1.5",
    packages=find_packages(),
    install_requires=[],
    author="Md Abu Salehin",
    author_email="mdabusalehin123@gmail.com",
    description="PyBrKarma - Python with Braces Runtime Transformer",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/Salehin-07/PyBrKarma",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "pybr = pybraces.__main__:main",
        ]
    },
)