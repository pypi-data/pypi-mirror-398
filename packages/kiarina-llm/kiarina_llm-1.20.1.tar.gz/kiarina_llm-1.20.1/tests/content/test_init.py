import pytest

import kiarina.llm.content as content


def test_getattr_invalid_name():
    with pytest.raises(
        AttributeError,
        match="module 'kiarina.llm.content' has no attribute 'NonExistentClass'",
    ):
        content.NonExistentClass
