from setuptools import setup, find_packages

setup(
    name="pyb-assistent",
    version="0.1.3",
    author="xqrto",
    description="PyB PyPi build assist",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "pyb-d=pyb_d.cli:create_pyb_bat",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
