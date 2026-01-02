#!/usr/bin/env python3
"""PyAutokit setup script for PyPI distribution."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read requirements
requirements = []
with open("requirements.txt") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            # Exclude dev dependencies
            if not any(dev in line for dev in ["pytest", "black", "flake8", "mypy"]):
                requirements.append(line)

setup(
    name="pyautokit",
    version="1.0.0",
    author="George Pricop",
    author_email="contact@georgepricop.com",
    description="Python Automation Toolkit - Complete CLI utilities for everyday tasks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Gzeu/pyautokit",
    project_urls={
        "Bug Tracker": "https://github.com/Gzeu/pyautokit/issues",
        "Documentation": "https://github.com/Gzeu/pyautokit/blob/main/README.md",
        "Source Code": "https://github.com/Gzeu/pyautokit",
        "Examples": "https://github.com/Gzeu/pyautokit/tree/main/examples",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Natural Language :: English",
    ],
    keywords=[
        "automation",
        "cli",
        "utilities",
        "file-organizer",
        "web-scraper",
        "email-automation",
        "backup",
        "blockchain",
        "crypto",
        "security",
        "data-processing",
        "productivity",
        "playwright",
        "browser-automation",
        "testing",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "watch": [
            "watchdog>=3.0.0",
        ],
        "browser": [
            "playwright>=1.40.0",
            "pytest-asyncio>=0.21.0",
        ],
        "all": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "watchdog>=3.0.0",
            "playwright>=1.40.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pyautokit=pyautokit.__main__:main",
            "pyautokit-organizer=pyautokit.file_organizer:main",
            "pyautokit-scraper=pyautokit.web_scraper:main",
            "pyautokit-email=pyautokit.email_automation:main",
            "pyautokit-backup=pyautokit.backup_manager:main",
            "pyautokit-logs=pyautokit.log_analyzer:main",
            "pyautokit-data=pyautokit.data_processor:main",
            "pyautokit-security=pyautokit.security_utils:main",
            "pyautokit-crypto=pyautokit.blockchain_monitor:main",
            "pyautokit-github=pyautokit.github_utils:main",
            "pyautokit-browser=pyautokit.playwright_utils:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
