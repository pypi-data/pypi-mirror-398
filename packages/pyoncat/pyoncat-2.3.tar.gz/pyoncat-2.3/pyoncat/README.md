Welcome to PyONCat, a Python client designed to facilitate interaction with the ONCat API.

## Introduction

[ONCat](https://oncat.ornl.gov) is a data cataloging system that assists scientists and researchers in managing and navigating their data. It aggregates information from various systems about datafiles, experiments and users, and offers a more convenient and manageable way to access neutron data and associated metadata.

The `pyoncat` package serves as a Python client to more easily interact with the ONCat API.  It is not required but is recommended if you are using Python.

## Installation

### Requirements

- Python version: `>=3.7, <4`
- Python packages: `requests`
- Optional packages for authenticated API access: `oauthlib`, `requests-oauthlib`

### Installing with pip

For basic unauthenticated installation, use the following command:

```sh
pip install pyoncat
```

To install the package with support for the authenticated version of the API, use the following command:

```sh
pip install pyoncat oauthlib requests-oauthlib
```

### Installing with Conda

Alternatively, a Conda package is available up on [Anaconda](https://anaconda.org/oncat/pyoncat).

## Usage

### Authenticating with the API

To use the authenticated version of the API, you need to obtain credentials from an ONCat administrator. Please contact ONCat Support at [oncat-support@ornl.gov](mailto:oncat-support@ornl.gov) to request credentials.

### Examples

For usage examples, please refer to the API documentation at [oncat.ornl.gov](https://oncat.ornl.gov).

## Getting Help

If you encounter any issues or require assistance with the `pyoncat` package, please reach out to the ONCat Support at [oncat-support@ornl.gov](mailto:oncat-support@ornl.gov).

## Resources

- [Official Documentation](https://oncat.ornl.gov)

Thank you for using PyONCat!
