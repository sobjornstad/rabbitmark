"""
setup.py -  setuptools configuration for esc
"""

import setuptools

# pylint: disable=invalid-name
long_description = "RabbitMark is a dumb bookmark manager."
#with open("README.md", "r") as fh:
#    long_description = fh.read()

setuptools.setup(
    name="rabbitmark",
    version="0.1.0",
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
        'windows-curses; platform_system == "Windows"',
    ],
    entry_points={
        "console_scripts": [
            "rabbitmark = rabbitmark.__main__",
        ],
    },
    python_requires='>=3.7',
)
