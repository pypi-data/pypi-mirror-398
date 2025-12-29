from setuptools import setup, find_packages

setup(
    name="textnotes",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.7",
    author="AnushaCoder",
    author_email="anushacoder02@gmail.com",
    description="Convert plain text into summaries, notes, flashcards, JSON, topic groups.",
    license="MIT",

    project_urls={
        "Source Repository": "https://github.com/anushacoder02/textnotes",
    },

    entry_points={
        "console_scripts": [
            "textnotes = textnotes.__main__:main"
        ]
    },
)
