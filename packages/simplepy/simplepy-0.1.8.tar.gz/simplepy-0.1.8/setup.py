from setuptools import setup, find_packages

setup(
    name="simplepy",               # MUST match PyPI name
    version="0.1.8",               # CHANGE every release
    packages=find_packages(),
    description="Simple Python utilities",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/GeniusVoid/simplepy",
    author="Vibhor Kumar",
    python_requires=">=3.7",
)
