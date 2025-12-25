from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lubit",
    version="0.1.0",
    author="Lubit",
    author_email="api@lubit.com",
    description="Official Python client for the Lubit Energy Prediction Market API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lubit-com/python-lubit",
    project_urls={
        "Bug Tracker": "https://github.com/lubit-com/python-lubit/issues",
        "Documentation": "https://lubit.com/api-docs",
        "Source": "https://github.com/lubit-com/python-lubit",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
    ],
    keywords="lubit energy prediction market api trading electricity",
)
