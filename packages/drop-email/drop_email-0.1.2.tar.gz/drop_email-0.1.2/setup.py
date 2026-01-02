from setuptools import setup, find_packages
from pathlib import Path

# Read README if it exists
readme_file = Path(__file__).parent / "README.md"
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "A package to send data (dict, list, pandas DataFrame) as beautiful HTML emails"

setup(
    name="drop_email",
    version="0.1.2",
    author="Delin Qu",
    author_email="delin.qu@gmail.com",
    description="A package to send data (dict, list, pandas DataFrame) as beautiful HTML emails",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DelinQu/drop_email",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pandas>=1.3.0",
        "pyyaml>=5.4.0",
    ],
    include_package_data=True,
    package_data={
        "drop_email": ["config.yaml.example"],
    },
    entry_points={
        "console_scripts": [
            "drop_email=drop_email.cli:main",
        ],
    },
)

