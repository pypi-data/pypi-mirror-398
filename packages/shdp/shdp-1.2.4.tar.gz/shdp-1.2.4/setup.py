"""Setup script for the shdp (Streamline Hyperlink Dynamic Protocol) package."""

from setuptools import find_namespace_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

try:
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = [
            line.strip() for line in fh if line.strip() and not line.startswith("#")
        ]
except UnicodeDecodeError:
    with open("requirements.txt", "r", encoding="utf-16") as fh:
        requirements = [
            line.strip() for line in fh if line.strip() and not line.startswith("#")
        ]

setup(
    name="shdp",
    version="1.2.4",
    author="Devling",
    author_email="contact@devling.fr",
    description="Streamline Hyperlink Dynamic Protocol",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/StanyslasBouchon/shdp-py",
    packages=find_namespace_packages(include=["shdp", "shdp.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    data_files=[
        ("", ["requirements.txt"]),
    ],
    package_data={
        "shdp": ["py.typed"],
    },
)
