#!/usr/bin/env python

try:
    from setuptools import setup, find_packages
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages


setup(
    name = "xunlei",
    version = "0.1",
    license = 'BSD',
    description = "Xunlei project provides basic api for xunlei lixian",
    py_modules = ['xunlei'],
    scripts = ['xunlei_cli'],
    install_requires = ['BeautifulSoup', 'mechanize'],
)
