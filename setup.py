#!/usr/bin/env python3
"""
Setup script for Twitter MCP Server - OAuth 2.0
"""

from setuptools import setup, find_packages
import os

# قراءة README
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# قراءة requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="x-twitter-mcp",
    version="2.0.0",
    author="Twitter MCP Team",
    author_email="team@example.com",
    description="Twitter MCP Server with OAuth 2.0 support",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/x-twitter-mcp-server",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
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
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.991",
        ],
        "production": [
            "gunicorn>=20.1.0",
            "psycopg2-binary>=2.9.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "x-twitter-mcp-server=x_twitter_mcp.__main__:main",
            "twitter-mcp-server=x_twitter_mcp.__main__:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "twitter",
        "mcp",
        "oauth2",
        "api",
        "social-media",
        "fastapi",
        "tweepy"
    ],
    project_urls={
        "Bug Reports": "https://github.com/yourusername/x-twitter-mcp-server/issues",
        "Source": "https://github.com/yourusername/x-twitter-mcp-server",
        "Documentation": "https://github.com/yourusername/x-twitter-mcp-server#readme",
    },
)
