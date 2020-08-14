"""
setup.py -  setuptools configuration for esc
"""

import setuptools

# pylint: disable=invalid-name
long_description = "my des"
#with open("README.md", "r") as fh:
#    long_description = fh.read()

setuptools.setup(
    name="rabbitmark",
    version="0.1.0",
    author="Soren I. Bjornstad",
    author_email="contact@sorenbjornstad.com",
    description="a dumb bookmark manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://google.com",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'windows-curses; platform_system == "Windows"',
    ],
    #scripts=['package_scripts/esc'],
    python_requires='>=3.6',
)
