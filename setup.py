from setuptools import setup

setup(
    name="BibToolPB",
    version="1.0.0a1",

    py_modules=["bibtoolpb"],

    install_requires=[
        "Click",
        "prompt_toolkit",
        "pybtex"
    ],

    entry_points="""
        [console_scripts]
        bibtoolpb=bibtoolpb:cli
    """,

    author="Parantapa Bhattacharya",
    author_email="pb [at] parantapa [dot] net",

    description="BibToolPB is a bibtex management tool.",

    license="MIT",
)
