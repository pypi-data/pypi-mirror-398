import setuptools

with open("README.md", "r") as fh:
    description = fh.read()

setuptools.setup(
    name="my_first_package_nazmul",
    version="0.0.2",  # ← Update version!
    author="Nazmul Islam",
    author_email="nazmulislam45213@gmail.com",
    description="A small example package",
    long_description=description,
    long_description_content_type="text/markdown",
    url="https://github.com/Nazmul0005/my-first-package.git",
    packages=["my_first_package_nazmul"],  # ← Make sure this matches your folder name!
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)