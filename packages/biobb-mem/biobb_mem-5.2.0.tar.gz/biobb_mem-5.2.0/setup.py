import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="biobb_mem",
    version="5.2.0",
    author="Biobb developers",
    author_email="ruben.chaves@irbbarcelona.org",
    description="Biobb_mem is a complete code template to promote and facilitate the creation of new Biobbs by the community.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="Bioinformatics Workflows BioExcel Compatibility",
    url="https://github.com/bioexcel/biobb_mem",
    project_urls={
        "Documentation": "http://biobb-mem.readthedocs.io/en/latest/",
        "Bioexcel": "https://bioexcel.eu/"
    },
    packages=setuptools.find_packages(exclude=['adapters', 'docs', 'test']),
    package_data={'biobb_mem': ['py.typed']},
    install_requires=['biobb_common==5.2.0'],
    python_requires='>=3.10,<3.13',
    entry_points={
        "console_scripts": [
            "cpptraj_density = biobb_mem.ambertools.cpptraj_density:main",
            "fatslim_apl = biobb_mem.fatslim.fatslim_apl:main",
            "fatslim_membranes = biobb_mem.fatslim.fatslim_membranes:main",
            "gorder_aa = biobb_mem.gorder.gorder_aa:main",
            "gorder_ua = biobb_mem.gorder.gorder_ua:main",
            "gorder_cg = biobb_mem.gorder.gorder_cg:main",
            "lpp_assign_leaflets = biobb_mem.lipyphilic_biobb.lpp_assign_leaflets:main",
            "lpp_flip_flop = biobb_mem.lipyphilic_biobb.lpp_flip_flop:main",
            "lpp_zpositions = biobb_mem.lipyphilic_biobb.lpp_zpositions:main",
            "mda_hole = biobb_mem.mdanalysis_biobb.mda_hole:main",
        ]
    },
    classifiers=(
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: Unix"
    ),
)
