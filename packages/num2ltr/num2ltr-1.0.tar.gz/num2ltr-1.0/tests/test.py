# Modules
from testMain import TestSingle, TEST_TYPE
from src.num2ltr._constants import maxNumber

# Test just one number
testType = TEST_TYPE.ONE
TestSingle(testType, 0, maxNumber)

# Test all desided range [BE CAREFUL]
# testType = TEST_TYPE.ALL
# TestSingle(testType, 0, 10)