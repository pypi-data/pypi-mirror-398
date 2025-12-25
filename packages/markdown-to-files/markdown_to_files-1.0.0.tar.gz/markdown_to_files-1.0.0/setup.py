from setuptools import setup, find_packages
import os

def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), 'r', encoding='utf-8') as f:
        return f.read()

setup(
    name="markdown-to-files",
    version="1.0.0",
    author="Jahanzeb Ahmed",
    author_email="jahanzebahmed12pk@gmail.com",
    description="Generate project structures from markdown files",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/JahanzebAhmed12/project_maker",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "pyyaml>=6.0",
        "colorama>=0.4.0",
        "jinja2>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "mdf=mdf.cli:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "mdf": ["templates/*.j2"],
    },
    keywords="markdown, project, scaffolding, generator, template",
    project_urls={
        "Bug Reports": "https://github.com/JahanzebAhmed12/project_maker/issues",
        "Source": "https://github.com/JahanzebAhmed12/project_maker",
        "Documentation": "https://github.com/JahanzebAhmed12/project_maker#readme",
    },
)