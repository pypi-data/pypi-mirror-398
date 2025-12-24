from pathlib import Path
from setuptools import setup, find_packages

BASE_DIR = Path(__file__).parent

INFO = "RP To-Do is a command-line interface application built with Typer to help you manage your to-do list."

# Long description from README
long_description = (BASE_DIR / "README.md").read_text(encoding="utf-8")

setup(
  # Basic identity
  name="rptodo",
  version="0.1",

  # Author info
  author="CryptoKingXavier",
  author_email="cryptokingxavier001@gmail.com",

  # Project description
  summary=INFO,
  description=INFO,
  long_description=long_description,
  long_description_content_type="text/markdown",

  # URLs
  # url="",
  # project_urls={
  #   "Documentation": "",
  #   "Source": "",
  #   "Tracker": "",
  # },

  # Packaging
  packages=find_packages(exclude=("tests", "tests.*")),
  include_package_data=True,

  # Python Compatibility
  python_requires=">=3.10",

  # Runtime dependencies
  install_requires=[
    # Add dependencies here.
    "click",
    "typer",
    "wheel",
    "colorama",
    "shellingham",
    "python-dotenv",
  ],

  # Optional dependencies
  extras_require={
    "dev": ["pytest", "mypy", "twine", "snoop", "setuptools"],
  },

  # Entry points (CLI tools)
  entry_points={
    "console_scripts": [
      "rptodo = rptodo.__main__:main",
    ],
  },

  # License
  license="MIT",

  # Classifiers (PyPI SEO)
  classifiers=[
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Operating System :: OS Independent",
    "Topic :: Software Development :: Libraries",
  ],

  # Keywords (searchability)
  keywords="python packaging cli utilities todo",

  # Zip safety (usually True)
  zip_safe=False,
)
