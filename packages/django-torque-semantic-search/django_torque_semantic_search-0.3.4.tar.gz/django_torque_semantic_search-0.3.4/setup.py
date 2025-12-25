#!/usr/bin/env python

from distutils.core import setup

# We read version from here to make it easier to read for outside scripts
# (like release scripts)
main_ns = {}
with open("semantic_search/version.py") as ver_file:
    exec(ver_file.read(), main_ns)

with open("README.md", "r", encoding="utf-8") as readme:
    long_description = readme.read()

setup(
    name="django-torque-semantic-search",
    version=main_ns["__version__"],
    description="django app for torque semantic search",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Open Tech Strategies, LLC",
    author_email="frankduncan@opentechstrategies.com",  # For now, this works
    url="https://code.librehq.com/ots/mediawiki/semantic-search",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
    ],
    packages=[
        "semantic_search",
        "semantic_search.migrations",
    ],
    install_requires=[
        "django-torque",
        "pgvector",
        "orjson",
        "luqum",
        "ply",
        "langchain-text-splitters",
        "tenacity",
        "httpx",
        "tiktoken",
    ],
    extras_require={
        "dev": ["pytest"],
    },
    package_dir={"": "."},
    python_requires=">=3.11",
)
