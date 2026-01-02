# Modules
from ._functions import _joinByGroups

maxNumber = int(1e15-1) # e.g. 999999999999999 (int)
maxNStr = _joinByGroups(str(int(1e15-1))) # e.g. 999.999.999.999.999 (str)
maxNumberLen = len(str(maxNumber)) # e.g. 15 (int)