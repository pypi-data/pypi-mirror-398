from setuptools import setup, find_packages
from pathlib import Path

BASE_DIR = Path(__file__).parent

README = (BASE_DIR / "README.md").read_text(encoding="utf-8")

setup(
    name="apcloudy-pipeline",
    version="0.1.1",
    author="Fawad",
    author_email="fawadstar6@email.com",
    description="Scrapy pipeline & extensions for AP Cloudy (logs, stats, requests, items)",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/fawadss1/apcloudy-pipeline",
    license="MIT",

    packages=find_packages(exclude=("tests*",)),

    python_requires=">=3.8",

    install_requires=[
        "requests>=2.30.0"
    ],

    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: Scrapy",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],

    include_package_data=True,
    zip_safe=False,
)
