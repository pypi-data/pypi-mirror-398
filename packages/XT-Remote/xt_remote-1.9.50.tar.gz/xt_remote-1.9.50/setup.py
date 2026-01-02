from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="XT_Remote",
    version="1.9.50", 
    author="MrAhmadiRad",
    author_email="mohammadahmadirad69@gmail.com",
    description="A precise, async-safe, Telegram automation core (Python 3.8+)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MohammadAhmadi-R/XT_Remote",
    packages=find_packages(),
    install_requires=[
        "pyrogram>=2.0.106",
        "httpx>=0.27.0",
        "pytz>=2023.3",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: AsyncIO",
        "Topic :: Communications",
        "Topic :: Communications :: Chat",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
