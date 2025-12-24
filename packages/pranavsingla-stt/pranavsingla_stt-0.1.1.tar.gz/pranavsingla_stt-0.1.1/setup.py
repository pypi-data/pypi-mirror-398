from setuptools import setup, find_packages

setup(
    name='pranavsingla_stt',
    version='0.1.1',
    author='Pranav Singla',
    author_email='monikasingla27051982@gmail.com',
    description='A speech-to-text package by Pranav Singla',
)
packages = find_packages(),
install_requirement = [
    'selenium',
    'webdriver_manager'
]