from setuptools import setup, find_packages

setup(
    name="chekml-blackemperor",  # This is the name on PyPI
    version="0.1.1",
    packages=find_packages(),
    install_requires=[
        "torch>=1.9.0",
        "torchvision>=0.10.0",
        "aiohttp>=3.8.0",
        "websockets>=10.0",
        "google-api-python-client>=2.0.0",
        "google-auth-httplib2>=0.1.0",
        "google-auth-oauthlib>=0.4.0",
        "gdown>=4.0.0",
    ],
    entry_points={
        "console_scripts": [
            "chekml=chekml_blackemperor.cli:main",  # Command is still 'chekml'
        ],
    },
)
