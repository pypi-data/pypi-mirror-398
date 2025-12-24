"""Setup configuration for mindzie-api package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read version from __version__.py
version = {}
with open(this_directory / "mindzie_api" / "__version__.py") as fp:
    exec(fp.read(), version)

setup(
    name="mindzie-api",
    version=version["__version__"],
    author="Mindzie",
    author_email="support@mindzie.com",
    description="Official Python client library for Mindzie Studio API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mindzie/mindzie-api-python",
    project_urls={
        "Bug Tracker": "https://github.com/mindzie/mindzie-api-python/issues",
        "Documentation": "https://docs.mindzie.com/api/python",
        "Source Code": "https://github.com/mindzie/mindzie-api-python",
    },
    packages=find_packages(exclude=["tests*", "examples*", "docs*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Typing :: Typed",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "typing-extensions>=4.0.0;python_version<'3.10'",
        "urllib3>=1.26.0",
        "certifi>=2022.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.10.0",
            "responses>=0.23.0",
            "faker>=18.0.0",
            "black>=23.0",
            "flake8>=6.0",
            "mypy>=1.0",
            "isort>=5.0",
            "pre-commit>=3.0",
            "tox>=4.0",
            "sphinx>=6.0",
            "sphinx-rtd-theme>=1.0",
            "twine>=4.0",
            "build>=0.10.0",
        ],
        "async": [
            "aiohttp>=3.8.0",
            "aiofiles>=23.0",
        ],
        "azure": [
            "msal>=1.20.0",
            "azure-identity>=1.12.0",
        ],
    },
    keywords=[
        "mindzie",
        "api",
        "client",
        "studio",
        "process mining",
        "business intelligence",
        "data analysis",
        "workflow",
        "automation",
    ],
    include_package_data=True,
    zip_safe=False,
)