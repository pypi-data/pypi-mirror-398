from setuptools import setup, find_packages
import os

# Чтение README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mathutilspro",
    version="1.0.0",
    author="Ваше Имя",
    author_email="your.email@example.com",
    description="Библиотека для математических операций",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mathutilspro",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Education",
    ],
    python_requires=">=3.7",
    keywords="mathutilspro, mathematics, utilities, operations",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/mathutilspro/issues",
        "Source": "https://github.com/yourusername/mathutilspro",
    },
)