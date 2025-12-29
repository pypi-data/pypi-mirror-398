from setuptools import find_packages, setup

setup(
    name='sapnmeterdata',
    packages=find_packages(include=['sapnmeterdata']),
    version='0.0.1',
    description='tbc',
    author='bfulham',
    install_requires=['json', 'bs4', 'requests', 'nemreader'],
)