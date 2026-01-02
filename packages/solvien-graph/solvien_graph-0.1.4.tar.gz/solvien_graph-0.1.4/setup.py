from setuptools import setup, find_packages
import os

long_description = ""
if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()

setup(
    name="solvien-graph",
    version="0.1.4", 
    author="Yasin Polat",
    description="Professional data visualization library - Optimized for bioinformatics and scientific analyses (D3.js/Vega-Lite/Altair based)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Solvien-Open-Source/solvien-graph",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Visualization",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    # Bağımlılıkları doğrudan buraya yazarak hata riskini sıfıra indiriyoruz
    install_requires=[
        "altair>=5.0.0",
        "pandas>=1.0.0",
        "numpy>=1.20.0",
    ],
)