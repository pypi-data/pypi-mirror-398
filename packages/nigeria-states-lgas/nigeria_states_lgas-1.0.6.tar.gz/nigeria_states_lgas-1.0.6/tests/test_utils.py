import pytest
from nigeria_states_lgas import get_states, get_lgas, get_all, search_lga, search_states
import pytest


def test_get_states():
    states = get_states()
    assert isinstance(states, list)
    assert "Lagos" in states
    assert "FCT" in states

def test_get_lgas():
    lgas = get_lgas("Kano")
    assert isinstance(lgas, list)
    assert "Nasarawa" in lgas or "Dala" in lgas  # depends on your data
    assert get_lgas("NonexistentState") == []

def test_get_all():
    all_data = get_all()
    assert isinstance(all_data, dict)
    assert "Lagos" in all_data
    assert isinstance(all_data["Lagos"], list)

def test_search_lga():
    state = search_lga("Dala")
    assert isinstance(state, list)
    assert "Kano" in state or len(state) > 0

    state_none = search_lga("NonexistentLGA")
    assert state_none == []


def test_search_lga_case_insensitive():
    state = search_lga("dala")
    assert isinstance(state, list)
    assert "Kano" in state or len(state) > 0

    state_none = search_lga("nonexistentlga")
    assert state_none == []

def test_search_states():
    states = search_states("PLA")
    assert isinstance(states, list)


def test_search_lga_fuzzy():
    # fuzzy should match close spellings
    results = search_lga("Dala", fuzzy=True)
    assert isinstance(results, list)
    assert "Kano" in results


def test_search_states_fuzzy():
    results = search_states("Plateu", fuzzy=True)
    # 'Plateu' is a common misspelling of 'Plateau'
    assert isinstance(results, list)
    assert "Plateau" in results


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        search_lga(None)  # type: ignore
    with pytest.raises(ValueError):
        search_states(123)  # type: ignore
