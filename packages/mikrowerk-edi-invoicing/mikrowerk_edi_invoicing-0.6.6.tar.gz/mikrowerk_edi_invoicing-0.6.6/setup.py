#
# Copyright (c)
#    Gammadata GmbH
#    All rights reserved.
#
# Any use of this file as part of a software system by non Copyright holders
# is subject to license terms.

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    # Here is the module name.
    name="mikrowerk_edi_invoicing",

    # version of the module
    version="0.6.6",

    # Name of Author
    author="Mikrowerk a Gammadata Division",

    # your Email address
    author_email="info@mikrowerk.com",

    # #Small Description about module
    description="Parser for EDI invoices in CII or UBL format or plain pdf with LLM support",

    # Specifying that we are using markdown file for description
    long_description=long_description,
    long_description_content_type="text/markdown",

    packages=setuptools.find_packages(exclude=["tests_*", "tests", "pdfparser"]),

    package_dir={"": "."},
    include_package_data=True,
    package_data={'': ['*.yaml', '*.jinja2', '*.sh']},

    install_requires=[
        "lxml",
        "pypdf",
        "pytest",
        "flake8",
        "isort",
        "black",
        "coverage",
        "codecov",
        "factur-x==3.6",
        "jsonpickle~=4.0.1",
        "parameterized",
        "schwifty",
        "google-genai"
    ],

    license="GNU Affero General Public License v3 ",

    # classifiers like program are suitable for python3, leave as it is.
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
    ],
)
