#!/usr/bin/env python
# coding:utf-8
import os
from setuptools import setup, find_packages

with open(r"T:\New_PC\Import_Project\uploads\pyscreeps-arena_upload\pyscreeps-arena.md", 'r', encoding='utf-8') as f:
    long_description = f.read()
setup(
    name='pyscreeps-arena',
    version='0.5.7.5',
    description='Python api|interface to play game: Screeps: Arena.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author_email='2229066748@qq.com',
    maintainer="Eagle'sBaby",
    maintainer_email='2229066748@qq.com',
    packages=find_packages(),
    package_data={
        '': ['*.7z'],
    },
    license='Apache Licence 2.0',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    entry_points={
        'console_scripts': [
            'pyscreeps-arena=pyscreeps_arena:CMD_NewProject',
            'arena=pyscreeps_arena:CMD_NewProject',
            'psaui=pyscreeps_arena:CMD_OpenUI',
        ]
    },
    keywords=['python', 'screeps:arena', 'screeps'],
    python_requires='>=3.10',
    install_requires=[
        'pyperclip',
        'colorama',
        'py7zr',
        'chardet',
        'Transcrypt==3.9.1',
        'PyQt6',
        'mkdocs',
        'mkdocstrings[python]',
        'mkdocs-material',
    ],
)
