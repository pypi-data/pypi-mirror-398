from setuptools import setup, find_packages

setup(
    name="open-freefire",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "requests"
    ],
    author="Abdul Moeez",
    description="OpenFF: Fetch FF account info and ban status",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://pypi.org/project/open-ff/",
    python_requires=">=3.7",
)
