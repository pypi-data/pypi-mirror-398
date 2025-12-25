# Python
import random
from pathlib import Path
from enum import Enum

# Syspath append folder "src"
import sys
parentFolder = Path.cwd() / "src"
sys.path.append(parentFolder.__str__())

# Modules
from main import main
from utils.functions import *

class TEST_TYPE(Enum):
    ONE = 1
    ALL = 2
    FILE = 3

class TestMain:
    def __init__(self, testType : TEST_TYPE, start = 0, end = 0):
        if testType == TEST_TYPE.ONE:
            self.__oneRand(start, end)
            
        elif testType == TEST_TYPE.ALL:
            self.__allRange(start, end)

        elif testType == TEST_TYPE.FILE:
            self.__fromFile("files/test.txt")

    def __oneRand(self, start, end):
        nTest = random.randint(start, end)
        self.endTesting = 's'

        print(f"TESTING... VALUE {nTest}")
        main(True, str(nTest), 's')
        print("\n")

    def __allRange(self, start, end):
        print(f"TESTING VALUES FROM {start} to {end}\n")

        for i in range(start, end+1):
            main(True, str(i), 's')

    def __fromFile(self, file):
        file_path = Path(__file__).resolve().parent / file

        with open(file_path) as f:

            print(f"TESTING VALUES FROM {f.name}\n")
            content = f.read().split("\n")
            for i in content:               
                print(joinByGroups(str(i)) + ": ", end='')
                main(True, str(i), 's')