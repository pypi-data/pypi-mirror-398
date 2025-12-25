# Pyton
import pytest

# Modules
from core.processor import number_to_letters
from tests.helpers.read_tests_file import readFile

# Read input file containing all tests
data = readFile('test1.yml')

@pytest.mark.parametrize("input, expected", data)
def test_file(input, expected):
    assert number_to_letters(str(input)) == expected