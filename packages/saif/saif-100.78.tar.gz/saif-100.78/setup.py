from setuptools import setup, find_packages

# Simple description without markdown formatting
LONG_DESCRIPTION = """
Saif Library - A Python library about Saif's love for Myheer

Installation:
pip install saif

Usage:
import saif
print(saif.loveWithWhom())  # Returns: Myheer
print(saif.inLove())        # Returns: True
print(saif.love_poem())     # Returns a beautiful love poem

Features:
- Check love status
- Get love quotes
- Check compatibility
- Love timeline
- Secret messages

Saif is in Love with Myheer. Forever. ❤️
"""

setup(
    # Basic package info
    name="saif",
    version="100.78",
    author="Saif",
    author_email="saifullahanwar00040@gmail.com",  # REPLACE WITH YOUR EMAIL
    
    # Description
    description="Saif loves Myheer - A Python library of eternal love",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/plain",  # Using plain text to avoid errors
    
    # Package structure
    packages=find_packages(),
    
    # Python requirements
    python_requires=">=3.6",
    
    # PyPI categories
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
    ],
    
    # Keywords for search
    keywords=["love", "saif", "myheer", "romance", "relationship", "eternal"],
    
    # No dependencies required
    install_requires=[],
    
    # Optional URLs (remove if you don't want them)
    # url="https://example.com",  # Optional
    # project_urls={  # Optional
    #     "Bug Reports": "https://example.com/issues",
    #     "Source": "https://example.com/source",
    # }
)