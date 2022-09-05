"""Test about the indexer."""

import pytest
import dataclasses
import propt.adapters.indexer as indexer


@pytest.fixture
def collection_dict() -> list[dict[str, int]]:
    return [{"foo": 23, "bar": 42}, {"foo": 45, "bar": 68}]


@dataclasses.dataclass
class Something:
    foo: int
    bar: str


@pytest.fixture
def collection_dataclass() -> list[Something]:
    return [
        Something(foo=12, bar="douze"),
        Something(foo=42, bar="quarante-deux"),
    ]


def test_1to1_collection_dict(collection_dict):
    indexer_obj = indexer.OneToOneIndexer(lambda x: x["foo"])
    indexer_obj.set_collection(collection_dict)
    assert indexer_obj[23] == {"foo": 23, "bar": 42}


def test_1to1_collection_dataclass(collection_dataclass):
    indexer_obj = indexer.OneToOneIndexer(lambda x: x.foo)
    indexer_obj.set_collection(collection_dataclass)
    assert indexer_obj[42] == Something(**{"foo": 42, "bar": "quarante-deux"})


def test_multi_to_multi_collection():
    collection = [
        {"keys": (12, 24), "name": "blah"},
        {"keys": (24, 123), "name": "pouf"},
    ]
    obj_indexer = indexer.MultiToMultiIndexer(lambda x: x["keys"])
    obj_indexer.set_collection(collection)
    assert obj_indexer[24] == collection
    assert obj_indexer[123] == [collection[1]]
