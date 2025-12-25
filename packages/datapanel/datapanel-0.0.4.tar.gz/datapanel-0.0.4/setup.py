# setup.py
from setuptools import setup, find_packages

setup(
    name="datapanel",
    version="0.0.4",
    author="ning9527",
    author_email="lizhi.guo@foxmail.com",
    description="datapanel.dev downloader",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)