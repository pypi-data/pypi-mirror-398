from setuptools import setup, find_packages

setup(
    name="textmonger",
    version="1.0.4",
    project_urls={
        "Source": "https://github.com/oceanthunder/textmonger",
    },
    description="A text analysis tool with readability, power word analysis, and NER visualization.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=[
        "spacy",
        "pyfiglet",
        "textstat",
        "tabulate",
        "textblob"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: The Unlicense (Unlicense)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    package_data={
        'textmonger': ['power_words.csv'],
    },
    entry_points={
        'console_scripts': [
            'textmonger=textmonger.project:main',
        ],
    },
)
