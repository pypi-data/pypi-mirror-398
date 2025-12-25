from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
from cloudpss import __version__
import os

os.system('git tag '+__version__)

setup(
    name='cloudpss',
    version=__version__,
    keywords=["cloudpss", "cloudpss-sdk"],
    description='cloudpss sdk',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT Licence",
    url='https://www.cloudpss.net',
    author='cloudpss',
    author_email='zhangdaming@cloudpss.net',
    packages=find_packages(),
    include_package_data=True,
    platforms="any",
    python_requires='>=3.7',
    install_requires=[
        'cffi', 'cryptography', 'cycler', 'pycparser', 'PyJWT', 'numpy',
        'PyYAML', 'requests', 'websocket-client>=1.4.0', 'pytz', 'deprecated','py-ubjson','aiohttp','zstandard'
    ],
)
