# Password Generator

Simple Python library to generate secure passwords.

## Installation
pip install password-generator-vh

## Usage
```python
from password_generator import PasswordGenerator

generator = PasswordGenerator(length=16)
password = generator.generate()
print(password)
