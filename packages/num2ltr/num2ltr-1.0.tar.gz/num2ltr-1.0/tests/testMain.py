# Python
import random
from pathlib import Path
from enum import Enum

# Syspath append base code folder (num2ltr_v1)
import sys
parentFolder = Path(__file__).parent.parent
sys.path.append(parentFolder.__str__())

# Modules
from src.num2ltr.processor import numberToLetters

class TEST_TYPE(Enum):
    ONE = 1
    ALL = 2
    FILE = 3

class TestSingle:
    def __init__(self, testType : TEST_TYPE, start = 0, end = 0):
        if testType == TEST_TYPE.ONE:
            self.__oneRand(start, end)
            
        elif testType == TEST_TYPE.ALL:
            self.__allRange(start, end)

    def __oneRand(self, start, end):
        nTest = random.randint(start, end)

        print(f"TESTING... VALUE {nTest}")
        print(numberToLetters(str(nTest)))
        print("\n")

    def __allRange(self, start, end):
        print(f"TESTING VALUES FROM {start} to {end}\n")

        for i in range(start, end+1):
            print(numberToLetters(str(i)))