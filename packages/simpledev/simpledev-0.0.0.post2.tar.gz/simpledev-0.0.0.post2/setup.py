from setuptools import setup, find_packages


def readme():
    with open('README.md', 'r') as f:
        return f.read()


setup(
    name='simpledev',
    version='0.0.0-002',
    author='Scholoch',
    author_email='alf.201105@gmail.com',
    long_description=readme(),
    long_description_content_type='text/markdown',
    url='',
    packages=find_packages(),
    install_requires=[],
    classifiers=[
        'Programming Language :: Python :: 3.13',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent'
    ],
    keywords='easy develop debug simpledev development debugging dev simple edad ',
    python_requires='>=3.6'
)

# python setup.py sdist bdist_wheel
# twine upload --repository pypi dist/*
