from setuptools import setup, find_packages
import codecs
import os

VERSION = '0.0.1'
DESCRIPTION = 'Returns the appropriate type of Git Commit Message.'
LONG_DESCRIPTION = 'A package that returns a type of commit message (fix/feat/major), based on changes provided to cached files in repository.'

# Setting up
setup(
    name="CommitMsgVerification",
    version=VERSION,
    author="nastka)",
    author_email="<anastasia.ganusina99@gmail.com>",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=['GitPython', 'importlib', 'sys', 'inspect', 'os', 'pathlib'],
    keywords=['python', 'git', 'commit', 'message'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)