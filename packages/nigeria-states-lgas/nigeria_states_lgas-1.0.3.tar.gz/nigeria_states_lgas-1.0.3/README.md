![PyPI](https://img.shields.io/pypi/v/nigeria-states-lgas)
![Python Versions](https://img.shields.io/pypi/pyversions/nigeria-states-lgas)
[![Python package](https://github.com/AETech-Research-Labs/nigeria-states-lgas-py/actions/workflows/python-tests.yml/badge.svg)](https://github.com/AETech-Research-Labs/nigeria-states-lgas-py/actions/workflows/python-tests.yml)
![License](https://img.shields.io/badge/license-MIT-green)

# Nigeria States & LGAs (Python Package)

A simple Python package containing all **36 Nigerian States + FCT** and their **Local Government Areas (LGAs)**.

## Installation

```bash
pip install nigeria-states-lgas
```

## Usage

```python
from nigeria_states_lgas import get_states, get_lgas, get_all, search_lga

# List all states
print(get_states())

# Get LGAs for a specific state
print(get_lgas("Kano"))

# Search which state(s) an LGA belongs to
print(search_lga("Ikot Ekpene"))

# Get the full dataset
all_data = get_all()
print(all_data["Lagos"])
```

## Features

- Provides all 36 Nigerian States + FCT.
- Lists all Local Government Areas (LGAs) for each state.
- Search for any LGA to find which state(s) it belongs to.
- Easy integration into Python projects.

## Contributing

Contributions are welcome! Please feel free to fork the repo and submit pull requests.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.