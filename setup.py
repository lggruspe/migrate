from pathlib import Path
import setuptools

setuptools.setup(
    name="migrate",
    version="0.0.0",
    author="Levi Gruspe",
    description="Python library/command-line program for running sqlite"
    + " migrations",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    url="https://github.com/lggruspe/migrate",
    packages=setuptools.find_packages(),
    classifiers=[
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "migrate=migrate.__main__:main"
        ]
    },
)
