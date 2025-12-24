import pathlib
from distutils.core import setup


HERE = pathlib.Path(__file__).parent.resolve()
LONG_DESCRIPTION = (HERE / "README.md").read_text(encoding="utf-8")

setup(
    name="repeatable",
    version="0.0.1",
    description="Python package to create generator-like objects that can be iterated over more than once.",
    author="Alastair Stanley",
    license="Apache-2.0",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    python_requires=">=3.9.0",
    install_requires=[
    ],
    project_urls={
        "Source": "https://github.com/optim-ally/repeatable.git",
    },
    classifiers=[
        # see https://pypi.org/classifiers/
        "Development Status :: 3 - Alpha",

        "Intended Audience :: Developers",
        "Topic :: Utilities",

        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
    ],
    package_dir={"": "src"},
    include_package_data=True,
)
