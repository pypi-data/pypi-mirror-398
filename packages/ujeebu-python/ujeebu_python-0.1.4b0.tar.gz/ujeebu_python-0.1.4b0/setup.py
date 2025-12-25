#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md', encoding='utf-8') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [ "requests" ]

test_requirements = [ ]

setup(
    author="Ujeebu",
    author_email='y.alhyane@gmail.com',
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    description="Ujeebu Python SDK to interact with Ujeebu API",
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme,
    long_description_content_type='text/markdown',
    include_package_data=True,
    keywords='ujeebu_python',
    name='ujeebu_python',
    packages=find_packages(include=['ujeebu_python', 'ujeebu_python.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/ujeebu/ujeebu-python',
    version='0.1.4-beta',
    zip_safe=False,
)
