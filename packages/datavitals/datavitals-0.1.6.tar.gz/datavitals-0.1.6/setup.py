from setuptools import setup, find_packages
from pathlib import Path

# -------------------------
# Read README safely
# -------------------------
BASE_DIR = Path(__file__).parent
README_PATH = BASE_DIR / "README.md"

long_description = ""
if README_PATH.exists():
    long_description = README_PATH.read_text(encoding="utf-8")

# -------------------------
# Setup Configuration
# -------------------------
setup(
    name="datavitals",
    version="0.1.6",
    author="Kamaleshkumar.K",
    author_email="kamaleshkumaroffi@gmail.com",
    description="A reusable Python library for data cleaning, ETL pipelines, and SQL query building",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kamaleshkumaroffi/datavitals",

    packages=find_packages(exclude=("tests*",)),

    python_requires=">=3.8",

    install_requires=[
        "pandas>=1.5.0",
    ],

    extras_require={
        "dev": [
            "pytest>=7.0.0",
        ]
    },

    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Software Development :: Libraries",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],

    license="MIT",

    keywords=[
        "data-engineering",
        "etl",
        "data-cleaning",
        "sql-builder",
        "pandas",
        "python-library",
    ],

    project_urls={
        "Source": "https://github.com/kamaleshkumaroffi/datavitals",
        "Tracker": "https://github.com/kamaleshkumaroffi/datavitals/issues",
        "LinkedIn": "https://www.linkedin.com/in/kamaleshkumaroffi",
    },
)
