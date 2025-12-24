from setuptools import setup, find_packages
import pathlib

# Read the contents of your README file
here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="volta-framework",
    version="0.1.2",
    description="A Python UI framework mimicking React",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/onyedibia/volta",
    author="Shinkilabs Nigeria Limited",
    author_email="shinkilabs@gmail.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords="framework, ui, react, python, frontend, ssr",
    packages=find_packages(exclude=["tests", "examples", "docs"]),
    python_requires=">=3.8, <4",
    install_requires=[],
    entry_points={
        'console_scripts': [
            'volta=volta.cli:main',
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/onyedibia/volta/issues",
        "Source": "https://github.com/onyedibia/volta",
    },
)
