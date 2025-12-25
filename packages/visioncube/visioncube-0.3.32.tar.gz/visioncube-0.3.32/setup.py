#!/usr/bin/python3
# -*- coding:utf-8 -*-

"""
author：yannan1
since：2023-09-20
"""

from setuptools import setup

setup(
    name='visioncube',
    packages=[
        'visioncube',
        'visioncube.functional',
        'visioncube.functional_cuda',
        'visioncube.operators',
        'visioncube.operators_cuda',
        'visioncube.recognition',
        'visioncube.measure'
    ],
    version='0.3.32',
    description='Image Processing Tool',
    author='liying, luzzi, yanaenen, xi',
    install_requires=[
        'numpy',
        'imgaug',
        'opencv-python',
        'opencv-contrib-python',
        'torch',
        'kornia',
        'torchvision',
        'PyYAML',
        'matplotlib',
        'shapely',
        'pyzbar',
        'pylibdmtx'
    ],
    platforms='any',
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
    include_package_data=True,
    zip_safe=False,
)
