from setuptools import setup, find_packages
import os

# Read README.md for long description
with open(os.path.join(os.path.dirname(__file__), "README.md"), "r", encoding="utf-8") as f:
    long_description = f.read()

# Read version from __init__.py
with open(os.path.join(os.path.dirname(__file__), "xst_cuc_xst", "__init__.py"), "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.strip().split("=")[1].strip().strip('"')
            break
    else:
        version = "0.0.1"

setup(
    name="xst-cuc-xst",
    version=version,
    author="Your Name",
    author_email="your.email@example.com",
    description="MCP Server implementation providing current time functionality with timezone support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/xst-cuc-xst",
    project_urls={
        "Source": "https://github.com/yourusername/xst-cuc-xst",
        "Documentation": "https://github.com/yourusername/xst-cuc-xst/README.md",
        "Issues": "https://github.com/yourusername/xst-cuc-xst/issues",
    },
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
        "Operating System :: OS Independent",
    ],
    keywords="mcp model-context-protocol server time timezone",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=3.7",
            "twine>=1.15",
            "wheel>=0.34",
        ],
    },
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "xst-cuc-xst=xst_cuc_xst.server:main",
        ],
    },
)
