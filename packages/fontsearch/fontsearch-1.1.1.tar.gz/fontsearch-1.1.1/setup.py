"""
Setup script for FontSearch package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="fontsearch",
    version="1.1.1",
    author="Michel Weinachter",
    author_email="michel.weinachter@example.com",
    description="Cross-platform font discovery and analysis library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/datamoc/fontsearch",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Text Processing :: Fonts",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No required dependencies - all optional
    ],
    extras_require={
        "full": [
            "fonttools>=4.0.0",  # For advanced font analysis and text filtering
            "pillow>=8.0.0",     # For ligature support and better font rendering
        ],
        "gui": [
            "pillow>=8.0.0",     # Required for GUI ligature controls and font rendering
        ],
        "text": [
            "fonttools>=4.0.0",  # For text support filtering
        ],
        "all": [
            "fonttools>=4.0.0",
            "pillow>=8.0.0",
        ],
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.0.0",
            "black>=21.0.0",
            "flake8>=3.8.0",
            "mypy>=0.800",
        ],
    },
    entry_points={
        "console_scripts": [
            "fontsearch=fontsearch.cli:main",
        ],
    },
    keywords="fonts typography system cross-platform discovery analysis",
    project_urls={
        "Bug Reports": "https://github.com/datamoc/fontsearch/issues",
        "Source": "https://github.com/datamoc/fontsearch",
        "Documentation": "https://github.com/datamoc/fontsearch/blob/main/README.md",
    },
)