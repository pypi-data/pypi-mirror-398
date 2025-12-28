# setup.py

from setuptools import setup, find_packages

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='zipher-sdk',
    version='0.4.3',
    description='Python SDK for programmatic access to the Zipher API',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Zipher Inc.',
    author_email='yoav@zipher.cloud',
    packages=find_packages(),
    install_requires=[
        "pydantic==2.11.3",
        "requests==2.32.3",
        "databricks-sdk==0.52.0"
    ],
    entry_points={
        "console_scripts": [
            "zipher=zipher.cli:main",
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
