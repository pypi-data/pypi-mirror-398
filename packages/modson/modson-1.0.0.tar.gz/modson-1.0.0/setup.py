from setuptools import setup
from pathlib import Path


setup(
    name="modson",
    version=Path(__file__).parent.joinpath("modson/VERSION").read_text(),
    keywords=["meson", "build", "mesonbuild", "modules", "wrapper", "custom", "modson"],
    description="Meson wrapper to load custom modules for complex build systems",
    long_description=Path(__file__).parent.joinpath("README.md").read_text(),
    long_description_content_type="text/markdown",
    url="https://github.com/alex-bouget/modson",
    author="alex-bouget",
    packages=["modson"],
    package_data={"modson": ["VERSION"]},
    entry_points={
        "console_scripts": [
            "modson = modson.__main__:main",
        ],

    },
    install_requires=[
        "meson>=1.0.0",
        "colorama>=0.4.6",
    ],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Build Tools",
    ]
)
