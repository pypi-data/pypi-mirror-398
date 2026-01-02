# Modules
from ._destructure_number import _groupByHundreds as groupByHundreds
from ._functions import _groupByThrees as groupByThrees
from . import _literals as literals

def number_to_letters(n):
    output = ""
    separator = ''
    groups = groupByThrees(n)
    groupsSize = len(groups)
    setMillions = True # Indicates when to set thousands of millions

    while groupsSize > 0:

        # Billions
        if groupsSize == 5:
            separator = literals.billions

            if groups[0] == '1':
                output += separator[1] + ' '
            else:
                output += f"{groupByHundreds(groups[0], True)}{separator[2]} "

        # Millions
        elif groupsSize == 3:
            # Has millions
            if setMillions:
                # if not output == "":
                separator = literals.millions

                if groups[len(groups)-3] == '1':
                    output += separator[1] + ' '
                else:
                    output += f"{groupByHundreds(groups[len(groups)-3], True)}{separator[2]} "
            
        # Thousands
        elif groupsSize == 2 or groupsSize == 4:
            # Has thousands
            if not groups[len(groups)-groupsSize] == '000':
                setMillions = True

                separator = literals.thousands[1]

                if groups[len(groups)-groupsSize] == '1' or groups[len(groups)-groupsSize] == '001':
                    output += separator + ' '
                else:
                    output += f"{groupByHundreds(groups[len(groups)-groupsSize], True)}{separator} "
            else:
                setMillions = False
        # Hundreds
        elif groupsSize == 1:
            output += groupByHundreds(groups[len(groups)-1])
        
        groupsSize -= 1

    return output.strip()