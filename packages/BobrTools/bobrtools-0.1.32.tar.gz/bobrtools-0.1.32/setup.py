from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().splitlines()

setup(
    name="BobrTools",
    version="0.1.32",
    description="Tools designed to simplify routine tasks for analysts, enabling faster "
                "and more efficient data processing and analysis",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Artsem Bobr",
    author_email="artyombobr@gmail.com",
    license="MIT",
    packages=find_packages(),
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
