import os
from setuptools import setup

current_dir = os.path.dirname(__file__)
init_path = os.path.join(current_dir, "src", "pixelpay", "__init__.py")

with open(init_path, "r") as version_file:
    [_, pkg_version] = version_file.readline().split(" = ")
    version = pkg_version.strip("\" \n")

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pixelpay-sdk",
    version=version,
    description=("PixelPay SDK toolkit."),
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=[
        "pixelpay",
        "pixelpay.base",
        "pixelpay.entities",
        "pixelpay.exceptions",
        "pixelpay.models",
        "pixelpay.requests",
        "pixelpay.resources",
        "pixelpay.responses",
        "pixelpay.services",
        "pixelpay.libraries",
    ],
    package_dir={"pixelpay": "src/pixelpay"},
    package_data={"pixelpay": ["assets/*.json"]},
    install_requires=["requests>=2.27.1"],
    keywords="pixelpay pixel pay sdk",
    author="Javier Cano",
    author_email="javier@pixel.hn",
    python_requires=">=3.6",
    classifiers=[
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
