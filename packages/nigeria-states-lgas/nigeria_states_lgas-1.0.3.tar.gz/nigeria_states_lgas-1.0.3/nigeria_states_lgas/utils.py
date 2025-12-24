import json
import json
import os
from typing import Dict, List, Optional
import difflib

# Path to JSON data
DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'nigeria_states_and_lgas.json')

# Internal cache for lazy loading
_DATA: Optional[Dict[str, List[str]]] = None


def _load_data() -> Dict[str, List[str]]:
    """Lazily load and return the dataset. Caches result on first load.

    Raises RuntimeError on missing or invalid data file.
    """
    global _DATA
    if _DATA is not None:
        return _DATA

    try:
        with open(DATA_PATH, 'r', encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as e:
        raise RuntimeError(f"Data file not found at {DATA_PATH}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Data file at {DATA_PATH} is not valid JSON") from e

    if not isinstance(data, dict):
        raise RuntimeError("Loaded data is not a mapping of state -> lgas")

    # ensure lists for LGAs
    cleaned: Dict[str, List[str]] = {}
    for state, lgas in data.items():
        if isinstance(lgas, list):
            cleaned[state] = lgas
        else:
            cleaned[state] = list(lgas)

    _DATA = cleaned
    return _DATA


def normalize_name(name: str) -> str:
    """Normalize a name for case-insensitive comparisons."""
    return name.strip().lower()


def get_states() -> List[str]:
    """Return a list of all Nigerian states (including FCT)."""
    data = _load_data()
    return list(data.keys())


def get_lgas(state: str) -> List[str]:
    """Return a list of all LGAs in a given Nigerian state (case-insensitive).

    Returns an empty list if the state is not found or input is invalid.
    """
    if not isinstance(state, str):
        raise ValueError("state must be a string")
    state_norm = normalize_name(state)
    data = _load_data()
    for s, lgas in data.items():
        if s.lower() == state_norm:
            return list(lgas)
    return []


def get_all() -> Dict[str, List[str]]:
    """Return a shallow copy of the full state -> LGA mapping."""
    return dict(_load_data())


def search_lga(lga_name: str, fuzzy: bool = False, cutoff: float = 0.6, max_results: int = 5) -> List[str]:
    """Search for an LGA and return a list of states.

    Parameters:
    - lga_name: LGA name or fragment to search for
    - fuzzy: if True, use fuzzy matching (difflib.get_close_matches)
    - cutoff: similarity cutoff for fuzzy matches (0..1)
    - max_results: max number of fuzzy matches to consider

    Returns a list of matching state names (may be empty).
    """
    if not isinstance(lga_name, str):
        raise ValueError("lga_name must be a string")
    name_norm = normalize_name(lga_name)
    data = _load_data()
    results: List[str] = []

    if fuzzy:
        # Build global list of lgas to match against
        lga_to_states: Dict[str, List[str]] = {}
        all_lgas: List[str] = []
        for state, lgas in data.items():
            for lga in lgas:
                lga_norm = lga.strip()
                all_lgas.append(lga_norm)
                lga_to_states.setdefault(lga_norm, []).append(state)

        close = difflib.get_close_matches(lga_name, all_lgas, n=max_results, cutoff=cutoff)
        for match in close:
            for s in lga_to_states.get(match, []):
                if s not in results:
                    results.append(s)
        return results

    # Non-fuzzy: exact or substring (case-insensitive)
    for state, lgas in data.items():
        for lga in lgas:
            lga_norm = lga.lower()
            if lga_norm == name_norm or name_norm in lga_norm:
                if state not in results:
                    results.append(state)
    return results


def search_states(prefix: str, fuzzy: bool = False, cutoff: float = 0.6) -> List[str]:
    """Return a list of states that match a prefix (case-insensitive) or fuzzy match."""
    if not isinstance(prefix, str):
        raise ValueError("prefix must be a string")
    prefix_norm = normalize_name(prefix)
    data = _load_data()

    if fuzzy:
        states = list(data.keys())
        return difflib.get_close_matches(prefix, states, n=len(states), cutoff=cutoff)

    return [state for state in data if state.lower().startswith(prefix_norm)]

