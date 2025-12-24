# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午2:31
# @Author  : fzf
# @FileName: setup.py
# @Software: PyCharm
from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="fast_generic_api",
    version="0.1.5",
    packages=find_packages(exclude=["venv", "venv.*"]),
    install_requires=[
        "fastapi",
        "tortoise-orm",
        "uvicorn",
        "watchfiles",
    ],
    author="fzf",
    description="A generic APIView base class for FastAPI with Tortoise ORM",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fzf54122/fast_generic_api",
    classifiers=[
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

