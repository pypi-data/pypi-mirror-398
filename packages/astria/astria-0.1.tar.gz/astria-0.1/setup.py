from setuptools import setup, find_packages

setup(
    name="astria",
    version="0.1",
    description="Astria is an email cleanup CLI tool that allows for fast deletion and newsletter unsubscribing.",
    author="Vallg-333",
    author_email="vallg8343@proton.me",
    packages=find_packages(),
    install_requires=["click", "bs4"],
    entry_points={
        "console_scripts": ["astria=astria.cli:astria"],
    },
)
