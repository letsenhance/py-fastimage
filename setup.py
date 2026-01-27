import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="py-fastimage-letsenhance", # Replace with your own username
    version="0.0.1",
    author="Let's Enhance",
    maintainer_email="antony.pererva@gmail.com",
    description="Read image format and size information from a few first bytes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/letsenhance/py-fastimage",
    packages=["fastimage"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
