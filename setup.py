"""
setup.py -  setuptools configuration for esc
"""

import setuptools
from rabbitmark.definitions import MYVERSION

# pylint: disable=invalid-name
long_description = "RabbitMark is a dumb bookmark manager."
#with open("README.md", "r") as fh:
#    long_description = fh.read()

setuptools.setup(
    name="rabbitmark",
    version=MYVERSION,
    author="Soren I. Bjornstad",
    author_email="contact@sorenbjornstad.com",
    description="powerful tag-based bookmark manager for the desktop",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sobjornstad/rabbitmark",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'SQLAlchemy~=1.3.5',
        'requests~=2.21.0',
        'PyQt5~=5.15.2',
        'pyperclip~=1.8.2',
        'tabulate==0.9.0',
    ],
    entry_points={
        "console_scripts": [
            "rabbitmark = rabbitmark.__main__:main",
        ],
    },
    python_requires='>=3.7',
)
