# Python
import pytest

# Modules
from src.num2ltr.processor import numberToLetters
from tests.helpers.read_tests_file import readFile

# Read input file containing all tests
data = readFile('test1.yml')

@pytest.mark.parametrize("input, expected", data)
def test_file(input, expected):
    assert numberToLetters(str(input)) == expected