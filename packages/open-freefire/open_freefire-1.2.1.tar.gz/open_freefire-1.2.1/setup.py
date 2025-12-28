from setuptools import setup, find_packages

setup(
    name="open-freefire",
    version="1.2.1",
    packages=find_packages(),
    entry_points = {
        "console_scripts": ["show_info = OpenFF.cli:main","is_ban = OpenFF.cli2:main"]
    },
    install_requires=[
        "requests",
        "argparse",
        "colorama",
        "datetime",
        "lolpython",
        "pyfiglet"
    ],
    author="Abdul Moeez",
    description="OpenFF: Fetch FF account info and ban status",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://pypi.org/project/open-freefire/",
    python_requires=">=3.7",
)
