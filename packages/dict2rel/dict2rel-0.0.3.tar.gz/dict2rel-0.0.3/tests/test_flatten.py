import pandas as pd
import polars as pl
import pytest

from dict2rel import flatten, inflate

from .data import EXAMPLE_SMALL


def test_flatten_basic():
    """A simple test for flattening an object"""
    flat = flatten(EXAMPLE_SMALL, lambda x: x)
    assert len(flat) == 1

    obj = flat[0]
    assert "name.first" in obj
    assert "matrix.0.0" in obj
    assert obj["matrix.0.0"] == EXAMPLE_SMALL["matrix"][0][0]


@pytest.mark.parametrize("provider", [pd.DataFrame, pl.DataFrame])
def test_flatten_basic_with_providers(provider):
    """Verify that providers are correctly used then flattening the data"""
    table = flatten(EXAMPLE_SMALL, provider)
    assert isinstance(table, provider)

    assert "name.first" in table
    assert table["name.first"].to_list() == [EXAMPLE_SMALL["name"]["first"]]


def test_flatten_and_then_inflate():
    """Ensure that the process of flattening and inflating are
    bijective and that the original value can be retrieved.
    """
    flat = flatten(EXAMPLE_SMALL, lambda x: x)
    inflated = inflate(flat)
    assert inflated[0] == EXAMPLE_SMALL
