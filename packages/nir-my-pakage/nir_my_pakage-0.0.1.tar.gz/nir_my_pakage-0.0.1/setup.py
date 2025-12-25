import setuptools

with open("README.md", "r") as fh:
    description = fh.read()

setuptools.setup(
    name="nir-my-pakage",
    version="0.0.1",
    author="Nazmul Islam",
    author_email="nazmulislam45213@gmail.com",
    description="A small example package",
    long_description=description,
    long_description_content_type="text/markdown",
    url="https://github.com/Nazmul0005/my-first-package.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)