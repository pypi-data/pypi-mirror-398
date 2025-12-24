"""A setuptools based setup module for instantgrade.

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
"""

from setuptools import setup, find_packages

# Read the long description from README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="instantgrade",  # Required
    version="0.1.15",  # Required - bumped to trigger release workflow
    description="An automated evaluation framework for Python notebooks and Excel assignments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chandraveshchaudhari/instantgrade",  # ✅ Updated repo URL

    author="Chandravesh Chaudhari",
    author_email="chandraveshchaudhari@gmail.com",

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Topic :: Software Development :: Testing",
        "Topic :: Education",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",

        # ✅ Updated Python versions
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],

    keywords="evaluation, grading, jupyter, notebook, excel, education, automated-grading, assignment-evaluation",
    package_dir={"": "src"},
    packages=find_packages(where="src"),

    # ✅ Enforce supported Python version (3.10 and above)
    python_requires=">=3.10, <4",

    install_requires=[
        "openpyxl>=3.0.0",
        "pandas>=1.0.0",
        "nbformat>=5.0.0",
        "nbclient>=0.5.0",
        "click>=7.0",
    ],

    extras_require={
        "xlwings": ["xlwings>=0.24.0"],
        "dev": ["pytest>=6.0", "black>=21.0", "flake8>=3.9"],
        "test": ["pytest>=6.0", "coverage>=5.5"],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-autobuild>=2024.0.0",
            "myst-parser>=2.0.0",
            "sphinx-autodoc-typehints>=1.25.0",
            "furo>=2024.1.29",
            "jupyter-sphinx>=0.5.0",
            "sphinx-copybutton>=0.5.2",
            "sphinx-design>=0.5.0",
            "linkify-it-py>=2.0.0",
        ],
        "all": [
            "xlwings>=0.24.0",
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.9",
            "coverage>=5.5",
            "sphinx>=7.0.0",
            "sphinx-autobuild>=2024.0.0",
            "myst-parser>=2.0.0",
            "sphinx-autodoc-typehints>=1.25.0",
            "furo>=2024.1.29",
            "jupyter-sphinx>=0.5.0",
            "sphinx-copybutton>=0.5.2",
            "sphinx-design>=0.5.0",
            "linkify-it-py>=2.0.0",
        ],
    },

    entry_points={
        "console_scripts": [
            # console command kept as 'instantgrade' but point to the
            # actual importable package (instantgrade) used in src/
            "instantgrade=instantgrade.cli.main:cli",
        ],
    },

    project_urls={
        "Bug Tracker": "https://github.com/chandraveshchaudhari/instantgrade/issues",
        "Documentation": "https://chandraveshchaudhari.github.io/instantgrade/",
        "Source": "https://github.com/chandraveshchaudhari/instantgrade/",
    },
)
