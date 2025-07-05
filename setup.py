"""
Setup script for Telegram File Downloader Bot.
"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# Read version information directly
def get_version_info():
    version_file = Path(__file__).parent / 'src' / 'version.py'
    with open(version_file, 'r') as f:
        exec(f.read(), globals())
    return globals()

version_info = get_version_info()

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="telegram-file-downloader-bot",
    version=version_info['__version__'],
    author=version_info['__author__'],
    author_email=version_info['__email__'],
    description=version_info['__description__'],
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url=version_info['__url__'],
    license=version_info['__license__'],
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "docker": [
            "docker>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "telegram-downloader-bot=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yml", "*.yaml", "*.json", "*.txt"],
    },
    zip_safe=False,
) 