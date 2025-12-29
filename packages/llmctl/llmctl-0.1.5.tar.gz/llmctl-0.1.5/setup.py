from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="llmctl",
    version="0.1.5",
    author="SM Sabbir Amin",
    author_email="sabbiramin.cse11ruet@gmail.com",
    description="A professional CLI tool for interacting with OpenAI and Anthropic LLMs with cost tracking",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sabbiramin113008/llmctl",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
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
        "openai>=1.0.0",
        "anthropic>=0.18.0",
        "colorama>=0.4.6",
    ],
    entry_points={
        "console_scripts": [
            "llmctl=cllm.cli:main",
        ],
    },
    keywords="llm cli openai anthropic claude gpt cost-tracking terminal",
    project_urls={
        "Bug Reports": "https://github.com/sabbiramin113008/llmctl/issues",
        "Source": "https://github.com/sabbiramin113008/llmctl",
    },
)