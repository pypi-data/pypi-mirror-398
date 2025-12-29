from setuptools import setup, find_packages

setup(
    name='yhlogin',
    version='1.0.12',
    packages=find_packages(),
    install_requires=[
        'httpx',
        'pyotp',
        'tenacity',
    ],
)