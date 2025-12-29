from setuptools import setup, find_packages

setup(
    name="Anti-gravity-qy",
    version="1766739.703.231",
    description="High-quality integration for https://antigravity.google/",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="SuperMaker",
    url="https://antigravity.google/",
    packages=find_packages(),
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
