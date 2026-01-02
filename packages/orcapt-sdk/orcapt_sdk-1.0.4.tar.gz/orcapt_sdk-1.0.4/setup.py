from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements from requirements.txt
def read_requirements():
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            requirements = []
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Skip comments and options
                    if not line.startswith("-"):
                        requirements.append(line)
            return requirements
    except FileNotFoundError:
        # Fallback to minimal requirements
        return [
            "requests>=2.25.0",
            "pydantic>=2.0.0",
        ]

setup(
    name="orcapt-sdk",
    version="1.0.4",
    author="Orca Team",
    author_email="support@orcapt.com",
    description="Clean, minimal package for Orca platform integration",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/Orcapt/orca-pip",
    packages=find_packages(),
    # Explicitly ensure builder.py is included
    py_modules=[],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Framework :: FastAPI",
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
        "web": [
            "fastapi>=0.100.0",
            "uvicorn>=0.20.0",
        ],
    },
    include_package_data=True,
    package_data={
        "orca": ["*.txt", "*.md"],
        "orca.patterns": ["*.py"],
    },
    keywords="orca, ai, chatbot, platform, integration, fastapi, real-time",
    project_urls={
        "Bug Reports": "https://github.com/Orcapt/orca-pip/issues",
        "Source": "https://github.com/Orcapt/orca-pip",
        "Documentation": "https://github.com/Orcapt/orca-pip#readme",
    },
)
