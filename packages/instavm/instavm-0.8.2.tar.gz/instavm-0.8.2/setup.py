# python setup.py sdist bdist_wheel
# twine upload --repository-url https://test.pypi.org/legacy/ dist/*
from setuptools import setup, find_packages

setup(
    name='instavm',
    version='0.8.2',
    packages=find_packages(),
    install_requires=[
        'requests',
    ],
    author='InstaVM Team',
    author_email='hello@instavm.io',
    description='A simple API client for code execution',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='http://instavm.io',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
