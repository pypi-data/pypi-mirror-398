import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="calculator-package-nazmul",
    version="0.0.1",
    author="Nazmul Islam",
    author_email="nazmulislam45213@gmail.com",
    description="A simple calculator package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Nazmul0005/calculator-package.git",
    packages=["calculator_package"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)