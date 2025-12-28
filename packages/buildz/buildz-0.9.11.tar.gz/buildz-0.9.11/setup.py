#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: Zzz(1309458652@qq.com)
# Description:

from setuptools import setup, find_packages

setup(
    name = 'buildz',
    version = '0.9.11',
    keywords='buildz',
    long_description=open('README.md', 'r', encoding="utf-8").read(),
    long_description_content_type='text/markdown',
    description = "配置读写（基于json格式进行简化）、ioc、以及其他工具代码。a json-base file format's read and write code by python, and codes to read and product object from configure file in such format(ioc), and other tool codes",
    license = 'Apache License 2.0',
    url = 'https://github.com/buildCodeZ/buildz',
    author = 'Zzz',
    author_email = '1309458652@qq.com',
    packages = find_packages(),
    include_package_data = True,
    platforms = 'any',
    install_requires = [],
)
