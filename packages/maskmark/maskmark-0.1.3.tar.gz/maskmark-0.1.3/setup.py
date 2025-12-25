#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：maskmark_py 
@File    ：setup.py
@IDE     ：PyCharm 
@Author  ：Handk
@Date    ：2025/7/21 19:02 
@Describe：
"""

import os
import sys
from codecs import open

from setuptools import setup

CURRENT_PYTHON = sys.version_info[:2]
REQUIRED_PYTHON = (3, 7)

if CURRENT_PYTHON < REQUIRED_PYTHON:
    sys.stderr.write(
        """
==========================
Unsupported Python version
==========================
This version of Maskmark requires at least Python {}.{}, but
you're trying to install it on Python {}.{}. To resolve this,
consider upgrading to a supported Python version.

""".format(
            *(REQUIRED_PYTHON + CURRENT_PYTHON)
        )
    )
    sys.exit(1)

# 'setup.py publish' shortcut.
if sys.argv[-1] == "publish":
    os.system("python setup.py sdist bdist_wheel")
    os.system("twine upload dist/*")
    sys.exit()

requires = [
    "pymupdf>=1.24.11",
    "pillow>=10.4.0",
    "filetype>=1.2.0",
    "toml>=0.10.2",
    "python-docx>=1.1.2",
    "gmssl>=3.2.2",
]
test_requirements = [
    "pytest-httpbin==2.1.0",
    "pytest-cov",
    "pytest-mock",
    "pytest-xdist",
    "PySocks>=1.5.6, !=1.5.7",
    "pytest>=3",
]

about = {}
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "src", "maskmark", "__version__.py"), "r", "utf-8") as f:
    exec(f.read(), about)

with open("README.md", "r", "utf-8") as f:
    readme = f.read()

setup(
    name='maskmark',
    version=about["__version__"],
    packages=['maskmark'],
    package_dir={"": "src"},
    url='https://git.hl.hdkwst.space/handk/maskmarkSDK_py',  # 替换为实际的项目URL
    license='GNU GENERAL PUBLIC LICENSE',
    author='handk',
    author_email='handk5373@163.com',  # 替换为实际的作者邮箱
    description='具备数据脱敏和数据水印功能的SDK包',
    long_description=readme,
    long_description_content_type='text/markdown',
    python_requires=">=3.7",
    install_requires=requires,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Security',
    ],
)
