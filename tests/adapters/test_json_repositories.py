"""Test about JSON repositories."""
import pathlib

import propt.adapters.json_repositories as json_repos


def test_load_json_file():
    """Test load_json_file."""
    path = pathlib.Path("pyanodons/item.json")
    data = json_repos.load_json_file(path)
    assert isinstance(data, dict)
