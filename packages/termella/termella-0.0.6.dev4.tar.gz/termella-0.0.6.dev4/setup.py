import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="termella",
    version="0.0.6.dev4",
    description="A Python library for rich text and beautiful formatting in the terminal.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="codewithzaqar",
    author_email="your.email@example.com",
    url="https://github.com/codewithzaqar/termella",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    python_requires=">=3.6",
    keywords="terminal, cli, colors, ansi, rich-text, formatting, ui, console",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Terminals",
        "Topic :: Utilities",
    ],
    project_urls={
        "Bug Tracker": "https://github.com/codewithzaqar/termella/issues",
        "Source": "https://github.com/codewithzaqar/termella",
    },
)