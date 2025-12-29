"""PoCSmith - AI-Powered Security Research Tool"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme = Path("README.md")
long_description = readme.read_text() if readme.exists() else ""

setup(
    name="pocsmith",
    version="1.0.0",
    description="AI-powered exploit and shellcode generation for security research",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Regaan",
    author_email="regaan48@gmail.com",
    url="https://github.com/noobforanonymous/PoCSmith",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "torch>=2.0.0",
        "transformers>=4.35.0",
        "peft>=0.7.0",
        "bitsandbytes>=0.41.0",
        "accelerate>=0.24.0",
        "click>=8.1.0",
        "requests>=2.31.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pocsmith=cli.main:cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

