#!/usr/bin/env python3
"""
Universal Search Tool - Setup Script

打包成可安装的 Python 包
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="universal-search-tool",
    version="1.2.0",
    author="Claude Code",
    author_email="claude@anthropic.com",
    description="🔍 零配置通用搜索工具 - 支持多引擎的命令行搜索",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/universal-search-tool",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    python_requires=">=3.7",
    install_requires=[
        "google-search-results>=2.4.2",
    ],
    entry_points={
        "console_scripts": [
            "universal-search=universal_search.cli:main",
            "universal-search-cli=universal_search.cli:main",
            "usearch=universal_search.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=["search", "cli", "google", "bing", "duckduckgo", "serpapi"],
    project_urls={
        "Bug Reports": "https://github.com/your-username/universal-search-tool/issues",
        "Source": "https://github.com/your-username/universal-search-tool",
        "Documentation": "https://github.com/your-username/universal-search-tool#readme",
    },
)