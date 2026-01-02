from setuptools import setup, find_packages
from pathlib import Path

# Read README if it exists
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as fh:
        long_description = fh.read()

setup(
    name="cherry_shared",
    version="0.1.22",
    packages=find_packages(),
    install_requires=[
        "web3",
        "pyrogram",
        "aiohttp",
    ],
    author="Mostafox",
    description="Cherry Bot shared utilities",
    long_description=long_description if long_description else "Cherry Bot shared utilities",
    long_description_content_type="text/markdown" if long_description else None,
    include_package_data=True,
    python_requires=">=3.11",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
