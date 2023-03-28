import sys
from os.path import join, dirname
from setuptools import setup, find_packages
sys.path.insert(0, join(dirname(__file__), 'src'))
from rdmysql import __version__


setup(
    name="rdmysql3",
    version=__version__,
    description="a mysql db layer for python3, based on nakagami/CyMySQL",
    author="Ryan Liu",
    author_email="azhai@126.com",
    url="https://github.com/azhai/rdmysql3",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Topic :: Database :: Front-Ends",
        "License :: OSI Approved :: MIT License",
    ],
    keywords=["mysql", "database", "model"],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        "cymysql>=0.0",
    ],
    dependency_links=[
        "git+ssh://git@github.com/nakagami/CyMySQL.git",
    ]
)
