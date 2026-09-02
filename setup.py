from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dofus-set-optimizer",
    version="0.1.0",
    description="Dofus set optimizer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="jdtibochab",
    author_email="",
    url="https://github.com/jdtibochab/dofus-set-optimizer",
    packages=find_packages(),
    install_requires=[
        "pygad",
        "pandas",
        "numpy",
        "ipykernel",
        "scikit-learn",
        "matplotlib"
    ],
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="dofus optimizer sets",
)
