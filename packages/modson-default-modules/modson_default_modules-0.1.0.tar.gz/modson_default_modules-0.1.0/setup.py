from setuptools import setup
from pathlib import Path


setup(
    name="modson-default-modules",
    version=Path(__file__).parent.joinpath("modson_default_modules/VERSION").read_text(),
    description="Some usefull custom Meson modules compatible with modson.",
    long_description=Path(__file__).parent.joinpath("README.md").read_text(),
    long_description_content_type="text/markdown",
    url="https://github.com/alex-bouget/modson-default-modules",
    author="alex-bouget",
    packages=["modson_default_modules"],
    package_data={"modson_default_modules": ["VERSION"]},
    install_requires=[
        "meson>=1.0.0",
        "modson>=1.0.0",
    ],
    entry_points={
        "modson.modules": [
            "java_d = modson_default_modules.java",
            "android_d = modson_default_modules.android",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Build Tools",
    ]
)
