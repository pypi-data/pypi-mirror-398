from setuptools import setup

setup(
    name="jinjatomic",
    version="0.0.1",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "edn-format",
        "jinja2",
        "requests",
    ],
)
