from setuptools import setup

try:
    with open("README.md", encoding="utf-8") as f:
        long_description = f.read()
except OSError:
    long_description = ""

setup(
    name="formtools-formprof",
    version="0.1.0",
    description="Profiler tool for FORM logs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tueda/formprof",
    py_modules=["formprof"],
    entry_points={
        "console_scripts": [
            "formprof = formprof:main",
        ]
    },
    python_requires=">=2.7,!=3.0.*,!=3.1.*",
    classifiers=[
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
)
