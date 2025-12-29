from setuptools import setup, find_packages

setup(
    name='yhlogin',
    version='1.0.11',
    packages=find_packages(),
    install_requires=[
        'httpx',
        'pyotp',
        'tenacity',
    ],
)