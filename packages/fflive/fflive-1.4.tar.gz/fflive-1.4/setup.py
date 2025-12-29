#!/usr/local/bin/python3

#############################################
# File Name: setup.py
# Author: mage
# Mail: 363604236@qq.com
# Created Time:  2018-9-9 19:17:34
#############################################


from setuptools import setup, find_packages

setup(
    name = "fflive",
    version = "1.4",
    keywords = ("python fflive"),
    description = "fflive python package url [https://github.com/jiashaokun/fflive]",
    long_description = "fflive python package",
    license = "MIT Licence",

    url = "https://github.com/jiashaokun/fflive",
    author = "SkeyJIA",
    author_email = "363604236@qq.com",

    packages = ['fflive'],
    include_package_data = True,
    platforms = "any",

    entry_points={
        'console_scripts': [
            'fflive=fflive_cli:main',
        ],
    },
)
