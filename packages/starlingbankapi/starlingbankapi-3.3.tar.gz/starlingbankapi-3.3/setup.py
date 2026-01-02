from setuptools import setup

setup(
    name="starlingbankapi",
    version="3.3",
    description="An unofficial Python package that provides access to parts of the Starling bank API. Designed to be used for personal use (i.e. using personal access tokens). Updated based on the 2019 codebase by Adam Dullage and the fork at https://github.com/rahulpdev/ to include Spaces support.",  # noqa
    url="https://github.com/richkershaw/starlingbankapi",
    author="Rich Kershaw",
    author_email="me@richkershaw.com",
    license="MIT",
    packages=["starlingbankapi"],
    install_requires=["requests"],
)
