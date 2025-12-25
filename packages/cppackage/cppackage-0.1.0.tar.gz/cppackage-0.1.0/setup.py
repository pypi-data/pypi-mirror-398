#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

with open('readme.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

# 包的基本信息
setup(
    name='cppackage',
    version='0.1.0',
    description='超品集团自用的Python包',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='team-数智组',
    author_email='m110135@163.com',
    url='https://github.com/example/CPpackage',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    python_requires='>=3.8',
    install_requires=[
        'pymysql',
        'pandas',
        'numpy',
    ],  
    entry_points={
        'console_scripts': [
            'cppackage=CPpackage.core:main',
        ],
    },
)
