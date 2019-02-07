import os
from setuptools import setup, find_packages

# Utility function to read the README file.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'devpost-profile-exporter',
    version = '1.0.0',
    author = 'Tejas Shah',
    description = "A CLI tool for exporting a Devpost user's projects.",
    long_description=read('README.md'),
    license = "MIT",
    keywords = "devpost hackathon export",
    url = "https://github.com/tejashah88/devpost-profile-exporter",
    py_modules=['devpost-export'],
    install_requires=[
        'Click',
        'beautifulsoup4',
        'requests',
        'html2text'
    ],
    entry_points='''
        [console_scripts]
        devpost_export=devpost_export:cli
    ''',
)