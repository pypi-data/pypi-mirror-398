#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   setup.py
@Time    :   2024/09/02 11:35:51
@Author  :   nicholas wu 
@Version :   1.0
@Contact :   nicholas_wu@aliyun.com
@License :    
@Desc    :   None
'''

from setuptools import setup, find_packages

install_requires = []

setup(
    name="nict",
    version="0.3.3",
    python_requires=">=3.5",
    packages=find_packages(),
    author="NICHOLAS WU",
    author_email="nicholas_wu@aliyun.com",
    description="magicmind examples, An easy to use library to speed up computation (by parallelizing on multi CPUs).",
    long_description="就不告诉你.",
    url="",
    include_package_data=True,
    install_requires=install_requires,
    license="MIT",
)
