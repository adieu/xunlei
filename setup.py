#!/usr/bin/env python
from setuptools import setup, find_packages


setup(
    name = "xunlei",
    version = "0.1.1",
    license = 'BSD',
    description = "Basic API for Xunlei Lixian",
    author='Ivan Diao',
    author_email='adieu@adieu.me',
    url='http://github.com/adieu/xunlei',
    py_modules = ['xunlei'],
    scripts = ['xunlei_cli'],
    install_requires = ['BeautifulSoup', 'mechanize'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
        "Topic :: Communications :: File Sharing",
    ],
)
