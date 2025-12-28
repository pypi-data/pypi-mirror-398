from setuptools import setup, find_packages

setup(
    name="ising_toolkit",
    version="1.0.3",
    packages=find_packages(include=['ising_toolkit', 'ising_toolkit.*']),
    install_requires=[
        'requests>=2.22.0',
    ],
    python_requires='>=3.8',
    author="IsingTech",
    author_email="haojunjie@isingtech.com",
    description="Python SDK for Ising Cloud Service",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/isingcloud/ising-cloud-sdk",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)