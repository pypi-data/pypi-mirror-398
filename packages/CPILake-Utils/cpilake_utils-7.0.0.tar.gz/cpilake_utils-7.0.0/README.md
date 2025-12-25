
# CPILake_Utils

## Introduction

A lightweight internal Python library providing reusable email-sending utilities and helper functions for the Fabric Notebook.

This package is distributed as a Python wheel (`.whl`) and can be used across notebooks, scripts, or internal pipelines.

## Features

- Send emails via a simple POST API
- Supports multiple recipients
- Handles HTTP 200, 201, 202 as successful response codes
- Minimal dependencies (`requests` only)
- Includes a pure-Python hash function for alphanumeric strings

## Package Structure

common_functions/                    <- root folder
├─ CPILake_Utils/                    <- package folder
│  ├─ __init__.py                    <- import all functions here
│  └─ CPILake_Utils.py               <- all utilities go here (email, hash, etc.)
├─ pyproject.toml
└─ README.md


## Installation

# Install the wheel file directly
pip install CPILake-Utils-1.0.0-py3-none-any.whl

# OR
pip install build       # Install the build tool
python -m build         # Creates the .whl file in dist/
twine upload dist/CPILake-Utils-1.0.0-py3-none-any.whl

# Usage Example

pip install CPILake-Utils==1.0.0

# OR
from CPILake-Utils import send_email_no_attachment, hash_function, send_email_no_attachment_01

print(hash_function("test"))

status, response = send_email_no_attachment(
    {"to": ["user@domain.com"], "subject": "Hi", "body": "Test email"},
    endpoint_url="https://your-endpoint",
    access_token="YOUR_ACCESS_TOKEN"
)
print(status, response)

print(status)  # 200 or None
print(response) # Response text or skip response


# Upload to PyPI (Token-based Authentication)
-- upload it to PyPI using an API token instead of username/password

# Replace $env:PYPI_API_TOKEN with your PyPI API token (PowerShell)
twine upload dist/* -u __token__ -p $env:PYPI_API_TOKEN

This securely uploads all files in the dist/ folder, After upload, your package will be available at:
https://pypi.org/project/CPILake-Utils/1.0.0/

## Author

Abhilash Ibrahimpatnam

## Summary

This README includes:

1. Clean introduction and feature list  
2. Clear package structure explanation  
3. Local installation and build instructions  
4. PyPI install instructions  
5. Usage examples with both functions  
6. Token-based upload instructions for PyPI  
7. Dependencies and author info


## Clean old build artifacts
Remove-Item -Recurse -Force build, dist
Remove-Item -Recurse -Force *.egg-info


