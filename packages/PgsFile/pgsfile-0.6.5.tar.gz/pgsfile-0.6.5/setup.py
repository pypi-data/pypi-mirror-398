# -*- coding: utf-8 -*-
"""
Created on Tue Mar 21 20:03:48 2023

@author: Petercusin
"""

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="PgsFile",
    version="0.6.5",
    author="Dr. Guisheng Pan is an instructor at the School of Foreign Studies, Shanghai University of Finance and Economics (SUFE).",
    author_email="panguisheng@sufe.edu.cn",
    description="This module streamlines Python package management, script execution, file handling, web scraping, and multimedia downloads. It supports LLM-based NLP tasks like OCR, tokenization, lemmatization, POS tagging, NER, ATE, dependency parsing, MDD, WSD, LIWC, MIP analysis, text classification, and Chinese-English sentence alignment. Additionally, it generates word lists and data visualizations, making it a practical tool for data scraping and analysis—ideal for literary students and researchers.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Petercusin/PgsFile", 
    license="Educational free",
    install_requires=["pandas", "python-docx", "pip", "requests", "fake-useragent", "lxml", "pimht", "pysbd", "nlpir-python","pillow", "liwc"],
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Free For Educational Use",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)