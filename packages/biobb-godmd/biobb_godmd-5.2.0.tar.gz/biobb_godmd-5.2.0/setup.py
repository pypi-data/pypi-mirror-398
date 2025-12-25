import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="biobb_godmd",
    version="5.2.0",
    author="Biobb developers",
    author_email="adam.hospital@irbbarcelona.org",
    description="Biobb_godmd is a BioBB category for GOdMD tool (protein conformational transitions).",
    long_description="Biobb_godmd allows the calculation of protein conformational transitions using the GOdMD tool.",
    long_description_content_type="text/markdown",
    keywords="Bioinformatics Workflows BioExcel Compatibility Ensemble Protein Transitions GOdMD",
    url="https://github.com/bioexcel/biobb_godmd",
    project_urls={
        "Documentation": "http://biobb-godmd.readthedocs.io/en/latest/",
        "Bioexcel": "https://bioexcel.eu/",
    },
    packages=setuptools.find_packages(exclude=["docs", "test"]),
    package_data={"biobb_godmd": ["py.typed"]},
    install_requires=["biobb_common==5.2.0"],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "godmd_prep = biobb_godmd.godmd.godmd_prep:main",
            "godmd_run = biobb_godmd.godmd.godmd_run:main",
        ]
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: Unix",
    ],
)
