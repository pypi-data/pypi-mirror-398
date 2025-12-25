from pathlib import Path

from setuptools import find_packages, setup

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text() if (this_directory / "README.md").exists() else ""

setup(
    name="praisonaiwp",
    version="1.6.0",
    description="AI-powered WordPress content management framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Praison",
    author_email="your.email@example.com",
    url="https://github.com/MervinPraison/praisonaiwp",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "paramiko>=3.0.0",
        "click>=8.1.0",
        "PyYAML>=6.0",
        "requests>=2.31.0",
        "mysql-connector-python>=8.0.33",
        "rich>=13.0.0",
        "tqdm>=4.65.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "praisonaiwp=praisonaiwp.cli.main:cli",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="wordpress wp-cli automation content-management cms",
)
