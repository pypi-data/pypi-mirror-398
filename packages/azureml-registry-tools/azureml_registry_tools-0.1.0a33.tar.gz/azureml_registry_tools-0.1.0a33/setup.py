# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

"""Set up package."""

from setuptools import setup, find_packages

DEPENDENCIES = [
    "azure-identity<2.0",
    "ruamel-yaml>=0.17.21,<0.19",
    "diskcache~=5.6",
    "azure-ai-ml>=1.30.0,<2.0",
    "azureml-assets>=1.16.99,<2.0"
]

exclude_list = ["*.tests"]

setup(
    name='azureml-registry-tools',
    version="0.1.0a33",
    description='AzureML Registry tools and CLI',
    author='Microsoft Corp',
    license="https://aka.ms/azureml-sdk-license",
    packages=find_packages(exclude=exclude_list),
    include_package_data=True,
    install_requires=DEPENDENCIES,
    python_requires=">=3.9,<3.14",
    entry_points={
        'console_scripts': [
            'repo2registry = azureml.registry._cli.repo2registry_cli:main',
            'registry-mgmt = azureml.registry._cli.registry_syndication_cli:main',
        ],
    }
)
