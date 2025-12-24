import setuptools

VERSION = '1.3.0'

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()


setuptools.setup(
    name="PyMouseKey",
    version=VERSION,
    author="Chasss",
    description="A python package for handling keyboard and mouse inputs",
    long_description_content_type="text/markdown",
    long_description=long_description,
)
