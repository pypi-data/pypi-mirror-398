"""Setup script for ChunkOps CLI (fallback for older pip versions)"""

from setuptools import setup, find_packages

setup(
    name="chunkops",
    version="0.1.0",
    description="CLI tool for detecting duplicate content in PDF documents",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="ChunkOps",
    author_email="hello@chunkops.ai",
    url="https://chunkops.ai",
    packages=find_packages(),
    install_requires=[
        "PyMuPDF>=1.23.0",
        "sentence-transformers>=2.2.0",
        "tiktoken>=0.5.0",
        "langchain-text-splitters>=0.2.0",
    ],
    entry_points={
        "console_scripts": [
            "chunkops=chunkops_cli.cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

