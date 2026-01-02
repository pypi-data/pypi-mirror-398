from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

setup(
    name="stxdefender",
    version="1.0.1",
    description="Python Source Code Encryption Tool - Enterprise-grade protection for your Python source code",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="STXDefender Team",
    author_email="support@stxdefender.example.com",
    url="https://github.com/yourusername/stxdefender",  # Update with your repo URL
    py_modules=["stxdefender"],
    install_requires=[
        "cryptography>=41.0.0",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "stxdefender=stxdefender:main",
        ],
    },
    python_requires=">=3.8",
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
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Security :: Cryptography",
    ],
    keywords="encryption, python, source code protection, obfuscation, security",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/stxdefender/issues",
        "Source": "https://github.com/yourusername/stxdefender",
        "Documentation": "https://github.com/yourusername/stxdefender#readme",
    },
)

