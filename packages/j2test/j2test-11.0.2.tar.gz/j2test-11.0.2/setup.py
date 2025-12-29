from setuptools import setup, find_packages
import os
import codecs

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

setup(
    name="j2test",
    version="11.0.2",
    author="Anupam Singh",
    author_email="anupam936574@gmail.com",
    description="test",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    keywords="test",
)
