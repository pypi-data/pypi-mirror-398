import pytest

import kiarina.llm.run_context as content


def test_getattr_invalid_name():
    with pytest.raises(
        AttributeError,
        match="module 'kiarina.llm.run_context' has no attribute 'NonExistentClass'",
    ):
        content.NonExistentClass
