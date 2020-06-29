import os
from setuptools import setup, find_packages


META_DATA = dict(
    name = "warchest bot",
    version = "0.0.1",
    license = "MIT",
    python_requires='>3.5.1',
    author = "48cfu",
    
    url = "https://github.com/near/near-api-py",

    packages = find_packages(),

    install_requires = ["requests", "base58", "ed25519", 'gevent', 'numpy']
)

if __name__ == "__main__":
    setup(**META_DATA)

