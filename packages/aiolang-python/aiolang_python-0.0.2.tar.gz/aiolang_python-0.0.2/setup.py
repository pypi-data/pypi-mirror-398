from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="aiolang-python",
    version="0.0.2",
    author="stone",
    author_email="kissme.cloud@gmail.com",
    description="Translate Google Framework For Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.0",
        "aiofiles>=23.1.0"
    ],
    keywords="python translate google",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.9",
)