# Modules
from . import _literals as literals

def _groupByHundreds(n, isSpecialOne = False):
        output = ""
        isTenthOfTwo = isTenthOfOne = hasTens = False

        digits = len(n)
        nInt = int(n) # parse n to integer
        i = digits

        while i > 0: 
            # hundreds
            if i == 3:
                output += _getHundreds(n, digits)
                
            # tens
            elif i == 2:
                tens = n[digits-2:]
                tensFirstChar = tens[0]

                # Has tens
                if not tensFirstChar == '0':
                    hasTens = True

                    output += _getTens(tens, tensFirstChar)

                    # Special cases 11 - 16
                    if int(tens) in range(11, 16):
                        output += ' '
                        break

                    # When it's the ten of the 1
                    if tensFirstChar == '1':
                        isTenthOfOne = True
                        output  += 'z ' if int(tens) == 10 else 'ci' # It's number 10

                    # When it's the ten of the 2
                    elif tensFirstChar == '2':
                        isTenthOfTwo = True
                        output += 'e ' if int(tens) == 20 else 'i' # It's number 20

                    else:
                        output  += ' '
                    
            # units
            elif i == 1:
                nInt = int(n[digits - 1])
                unit = literals.units[nInt]
                
                # No unit required
                if digits > 1 and nInt == 0:
                    break

                # # More tens
                # elif 
                if hasTens:
                    if not (isTenthOfOne or isTenthOfTwo):
                        output += 'y '

                    # units when accent is required
                    if (isTenthOfOne or isTenthOfTwo) and (nInt == 2 or nInt == 3 or nInt == 6):
                        unit = literals.unitsExceptions[nInt]

                # When the text for the 'one' is special
                if isSpecialOne and nInt == 1:
                    unit = literals.unitsExceptions[1]
                    unit = unit.replace('u', 'ú') if isTenthOfTwo else unit

                output += unit + ' '
                
            i -= 1

        return output

def _getHundreds(n, digits):
    output = ""
    hundreds = n[digits-3:]
    hFirstChar = hundreds[0]
    hInt = int(hundreds)

    # Has hundreds
    if not hFirstChar == '0':
        for i in range(1, 10):
            if int(hFirstChar) == i:
                output += literals.hundreds[int(str(i) + '00')]

                if int(hFirstChar) == 1 and (hInt in range(101, 200)):
                    output += 'to'
                
                output += ' '
                break
        
    return output
    
def _getTens(tens, tFirstChar):
    output = ""
    tens = int(tens)

    if tens in range(11, 16):
        output += literals.tens[tens]
    else:
        # Loop through 1 - 9
        for i in range(1, 10):
            if int(tFirstChar) == i:
                output += literals.tens[int(str(i) + '0')]
                break

    return output
