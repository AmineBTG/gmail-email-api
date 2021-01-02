from setuptools import setup, find_packages

with open("README.md", "r") as readme:
    long_description = readme.read()

setup(

    # Define the library name, this is what is used along with `pip install`.
    name='gmail-email-api',

    # Define the author of the repository.
    author='Amine BOUTAGHOU',

    # Define the Author's email, so people know who to reach out to.
    author_email='boutaghouamine@gmail.com',

    # Define the version of this library.
    # Read this as
    #   - MAJOR VERSION 0
    #   - MINOR VERSION 1
    #   - MAINTENANCE VERSION 0
    version='0.1.0',

    # Here is a small description of the library. This appears
    # when someone searches for the library on https://pypi.org/search.
    description='A python client library used to fetch Gmail Emails content and attachments files data in an easy way.',

    # I have a long description but that will just be my README
    # file, note the variable up above where I read the file.
    long_description=long_description,

    # here are the packages I want "build."
    packages=find_packages(),

    # Here I can specify the python version necessary to run this library.
    python_requires='>=3.8',

    # Here is the URL where you can find the code, in this case on GitHub.
    url='https://github.com/AmineBTG/gmail-email-api.git'
)
