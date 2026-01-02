"""Setup script for apcloudy package."""

from setuptools import setup, find_packages
import os

# Read the contents of the README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


# Read version from __init__.py
def get_version():
    with open(os.path.join(this_directory, 'apcloudy', '__init__.py')) as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return '0.1.4'


setup(
    name='apcloudy',
    version=get_version(),
    author='Fawad Ali',
    author_email='fawadstar6@gmail.com',
    description='A Python client for interacting with the APCloudy platform',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/fawadss1/apcloudy',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.7',
    install_requires=[
        'requests>=2.32.4',
        'tabulate>=0.9.0',
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'black>=21.0',
            'flake8>=3.8',
            'mypy>=0.800',
        ],
    },
    entry_points={
        'console_scripts': [
        ],
    },
    keywords='apcloudy api client web scraping spiders',
    project_urls={
        'Bug Reports': 'https://github.com/fawadss1/apcloudy/issues',
        'Source': 'https://github.com/fawadss1/apcloudy',
        'Documentation': 'https://github.com/fawadss1/apcloudy#readme',
    },
)
