from setuptools import setup, find_packages

setup(
    name="JavaScriptNU",
    version="0.0.2",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[],
    author="Iven Boxem",
    description="JavaScript syntax in Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)