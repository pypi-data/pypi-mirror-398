from setuptools import setup, find_packages
from io import open


def read(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()


setup(
    name='ORD',
    version='1.8.12',
    author='Vladimir Smirnov',
    author_email='volodya@brandshop.ru',
    description='Module for working with the ATOL cash register driver',
    url='https://github.com/brandshopru',
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    packages=find_packages(),
)
