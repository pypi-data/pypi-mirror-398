#!/usr/bin/env python3

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    readme = fh.read()

from srtfu.version import version


setuptools.setup(
    name="SRTfu",
    version=version,
    author="Adrian of Doom ",
    author_email="spam@bad.show",
    description="Secure Reliable Transport",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/superkabuki/SRTfu",
    install_requires=[
    ],
    packages=setuptools.find_packages(),
    classifiers=[
	"License :: OSI Approved :: Sleepycat License",
        "Environment :: Console",
	"Natural Language :: English",
        "Operating System :: OS Independent",
	"Operating System :: Unix",
        "Operating System :: Other OS",
        "Operating System :: POSIX :: BSD :: OpenBSD",
        "Operating System :: POSIX :: BSD :: NetBSD",
        "Operating System :: POSIX :: Linux",
	"Operating System :: POSIX :: SCO",
        "Topic :: Multimedia :: Video",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    python_requires=">=3.9",
)
