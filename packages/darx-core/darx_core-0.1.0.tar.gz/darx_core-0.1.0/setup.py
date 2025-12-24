"""
Setup configuration for darx-core package
"""
from setuptools import setup, find_packages

# Read long description from README
try:
    with open('README.md', 'r', encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = 'DARX Core - Shared utilities for DARX microservices'

# Read dependencies from requirements.txt
try:
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
except FileNotFoundError:
    requirements = [
        'supabase>=2.0.0',
        'slack-sdk>=3.0.0',
        'google-cloud-storage>=2.0.0',
        'structlog>=24.0.0',
        'requests>=2.31.0',
    ]

setup(
    name='darx-core',
    version='0.1.0',
    author='Digital ArchiteX',
    author_email='mrvnrmro@gmail.com',
    description='Shared utilities and clients for DARX microservices',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/digitalarchitex/darx-core',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    python_requires='>=3.9',
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords='darx microservices utilities clients',
    project_urls={
        'Bug Reports': 'https://github.com/digitalarchitex/darx-core/issues',
        'Source': 'https://github.com/digitalarchitex/darx-core',
    },
)
