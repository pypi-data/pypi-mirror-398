from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="textnotes",
    version="0.1.1",  
    packages=find_packages(),
    python_requires=">=3.7",
    author="AnushaCoder",
    author_email="anushacoder02@gmail.com",
    description="Convert plain text into summaries, notes, flashcards, JSON, topic groups.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    project_urls={
        "Source Repository": "https://github.com/anushacoder02/Textnotes/",
    },
    entry_points={
        "console_scripts": [
            "textnotes = textnotes.__main__:main"
        ]
    },
)
