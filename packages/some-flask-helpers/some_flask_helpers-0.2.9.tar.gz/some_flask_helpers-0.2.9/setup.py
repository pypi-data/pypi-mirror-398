from os import path

from setuptools import setup

this_directory = path.abspath(path.dirname(__file__))

with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(this_directory, 'requirements.txt')) as f:
    install_requires = f.read().splitlines()


setup_params = {
    "python_requires": '>=3.10, <3.14',

    # standard setup configuration
    "name": "some_flask_helpers",
    "version": "0.2.9",
    "description": "Generic tools for Flask applications",
    "author": "Marcus Rickert",
    "author_email": "marcus.rickert@web.de",
    "url": "https://github.com/marcus67/some_flask_helpers",

    "install_requires": install_requires,

    "packages": ['some_flask_helpers'],
    "include_package_data": True,

    "long_description_content_type" : 'text/markdown',
    "long_description": long_description,
}

extended_setup_params = {
    # additional setup configuration used by CI stages
    "id": "some-flask-helpers",
}

extended_setup_params.update(setup_params)

if __name__ == '__main__':
    setup(**setup_params)
