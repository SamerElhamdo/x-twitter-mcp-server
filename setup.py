#!/usr/bin/env python3
"""
Setup script for X (Twitter) MCP Server
"""

from setuptools import setup, find_packages
import os

# قراءة README
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# قراءة المتطلبات
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="x-twitter-mcp",
    version="0.2.0",
    author="Rafal Janicki",
    author_email="rafal@kult.io",
    description="X (Twitter) MCP Server with OAuth 2.0 Authentication",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/rafaljanicki/x-twitter-mcp-server",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.10",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "x-twitter-mcp-server=x_twitter_mcp.server:run",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
