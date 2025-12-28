from setuptools import setup, find_packages
import os

def read_requirements():
    """Parse requirements.txt."""
    reqs = []
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r') as f:
            reqs = [line.strip() for line in f if line.strip()]
    return reqs

setup(
    name='grucli',
    version='3.3.4',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=read_requirements(),
    entry_points={
        'console_scripts': [
            'grucli = grucli.main:main',
        ],
    },
    author='grufr',
    description='A command-line interface for interacting with local and remote LLMs.',
    long_description=open('README.md').read() if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    url='https://github.com/grufr/grucli',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    package_data={
        'grucli': ['sysprompts/*'],
    },
    include_package_data=True,
)
