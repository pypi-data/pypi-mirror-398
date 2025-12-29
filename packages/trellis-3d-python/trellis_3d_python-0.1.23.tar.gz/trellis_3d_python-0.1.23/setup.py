from setuptools import setup, find_packages

setup(
    name="trellis-3d-python",
    version="0.1.23",
    packages=find_packages(),
    install_requires=[
        "torch",
        "numpy",
    ],
    author="Microsoft Corporation",
    author_email="t-jxiang@microsoft.com",
    description="TRELLIS is a large 3D asset generation model.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/microsoft/trellis",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
) 