import pytest

from src.core.errors import InputValidationError
from src.utils.validators import validate_question


def test_validate_question_ok():
    assert validate_question("  Hello world  ", 100) == "Hello world"


def test_validate_question_short():
    with pytest.raises(InputValidationError):
        validate_question(" ", 100)


def test_validate_question_long():
    with pytest.raises(InputValidationError):
        validate_question("a" * 101, 100)