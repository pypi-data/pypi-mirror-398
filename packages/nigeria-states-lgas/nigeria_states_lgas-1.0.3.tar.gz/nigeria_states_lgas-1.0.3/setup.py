from setuptools import setup, find_packages

setup(
    name="nigeria-states-lgas",
    version="1.0.3",
    description="A Python package with all Nigerian States and LGAs dataset",
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
    ],
    python_requires='>=3.6'
)
