"""JSON repositories for Factorio."""
from __future__ import annotations

import abc
import json
import pathlib
from collections.abc import Mapping
from typing import Any, TypeVar

import propt.domain.new_factorio.prototypes as prototypes
import propt.domain.new_factorio.repositories as repo_model


T = TypeVar("T", bound=prototypes.Prototype)


class JSONFactorioRepository(repo_model.Repository[T], metaclass=abc.ABCMeta):
    def __init__(self, filename: str):
        super().__init__()
        self.__filename = filename

    @abc.abstractmethod
    def build_object(self, data: Mapping[str, any]) -> T:
        """Build a Factorio object from its JSON dict representation."""

    def _load_file(self, json_directory: pathlib.Path) -> None:
        with open(json_directory / self.__filename) as f:
            data = json.load(f)
        for data_item in data.values():
            obj = self.build_object(data_item)
            self[obj.name] = obj
