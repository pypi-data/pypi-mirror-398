"""Setup script for mcp-runtime."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mcp-runtime",
    version="0.1.4",
    description="Simple Python library to connect LLM models with MCP (Model Context Protocol) servers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Aditya Jangam",
    author_email="adjangam9@gmail.com",
    license="MIT",
    packages=find_packages(exclude=["examples", "tests"]),
    python_requires=">=3.10",
    install_requires=[
        "jsonschema>=4.0.0",
        "aiohttp>=3.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
        "openai": ["openai>=1.0.0"],
        "gemini": ["google-generativeai>=0.3.0"],
        "claude": ["anthropic>=0.18.0"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords=["mcp", "model-context-protocol", "llm", "runtime", "tools", "functions"],
)

