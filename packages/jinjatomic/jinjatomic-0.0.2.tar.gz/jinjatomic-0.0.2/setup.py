from setuptools import setup

setup(
    name="jinjatomic",
    version="0.0.2",
    description="A Datomic REST API client for Python reliant on jinja2 templates for writing stringified edn.",
    url="https://github.com/lukal-x/jinjatomic",
    author="Luka L",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "edn-format",
        "jinja2",
        "requests",
    ],
)
