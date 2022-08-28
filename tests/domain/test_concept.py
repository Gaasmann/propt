"""Tests for Concept."""
import pytest

import propt.domain.concepts as concepts


def test_concept_are_immutable():
    """Check the concepts are really immutable."""
    item = concepts.Item(code=concepts.Code("code"), name="quantum")
    with pytest.raises(TypeError):
        item.code = "tutu"
