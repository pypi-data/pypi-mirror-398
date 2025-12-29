import codecs
import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

setup(
    name="thsdk",
    version="1.7.6",
    description="THSDK",
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=["thsdk"],
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=[
        "pandas>=1.3.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
    ],
    package_data={
        'thsdk': ['*', 'examples/*', "libs/darwin/*", "libs/linux/*", "libs/windows/*"],
    },
)
