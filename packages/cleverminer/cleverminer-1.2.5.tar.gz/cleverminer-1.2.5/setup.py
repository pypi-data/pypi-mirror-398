import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cleverminer",
    version="1.2.5",
    author="(C) Copyright 2020 - 2025 Petr Masa",
    author_email="code@cleverminer.org",
    description="Beyond apriori. CleverMiner is the package for enhanced association rule mining (eARM). Comparing to standard association rules, it is very enhanced, because the package implements the GUHA procedures that generalizes apriori and association rules in many ways. Rules are based on categorical data that can be easily visualized and interpreted. Their if-then with probability allows easy deployment by human realized processes. Interpretable & explainable knowledge mining.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://cleverminer.org",
    project_urls={
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Development Status :: 5 - Production/Stable",
	    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    install_requires=['progressbar2','pandas','numpy','matplotlib','seaborn'],
    python_requires=">=3.8"
)