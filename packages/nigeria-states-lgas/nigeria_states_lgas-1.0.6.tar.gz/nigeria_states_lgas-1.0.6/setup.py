from setuptools import setup, find_packages
from pathlib import Path

here = Path(__file__).parent
long_description = ""
readme = here / "README.md"
if readme.exists():
    long_description = readme.read_text(encoding="utf-8")

setup(
    name="nigeria-states-lgas",
    version="1.0.6",
    description="A Python package with all Nigerian States and LGAs dataset",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AETech Research Labs",
    author_email="info@aetechlabs.com",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'nigeria_states_lgas': ['data/*.json', 'data/*.csv', 'data/*.sql'],
    },
    url="https://github.com/aetechlabs/nigeria-states-lgas-py",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
    ],
    python_requires='>=3.7',
    keywords=["nigeria", "states", "lgas", "geodata", "nigeria-states"],
    project_urls={
        'Documentation': 'https://github.com/aetechlabs/nigeria-states-lgas-py#readme',
        'Source': 'https://github.com/aetechlabs/nigeria-states-lgas-py',
        'Tracker': 'https://github.com/aetechlabs/nigeria-states-lgas-py/issues',
    },
    license="MIT",
    entry_points={
        'console_scripts': [
            'nigeria-states-lgas=nigeria_states_lgas.cli:main',
        ],
    },
)
