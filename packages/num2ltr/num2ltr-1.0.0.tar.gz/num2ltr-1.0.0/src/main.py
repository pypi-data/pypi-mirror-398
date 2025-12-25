# Modules
# from utils.functions import groupByThrees
from num2ltr.processor import numberToLetters
from num2ltr._constants import maxNStr
# import literals

def main(isTesting = False, nTest = '', endExec = 'n'):
    stop = 'n'

    while (not stop == 's'):
        output = ""
        # isTenthOfTwo = isTenthOfOne = hasTens = False

        # maxNumber = '.'.join(groupByThrees(str(int(1e12-1))))
        n = nTest if isTesting else input(f"Ingresar un numero entre 0 - {maxNStr}: ")
        output =  numberToLetters(n)
        # digits = len(n) # TODO: Remove initial cero
        # nInt = int(n) # parse n to integer
        # i = digits

        # separator = ''
        # groups = groupByThrees(n)
        # groupsSize = len(groups)
        # setMillions = True # Indicates when to set thousands of millions

        # while groupsSize > 0:

        #     # Billions
        #     if groupsSize == 5:
        #         separator = literals.billions

        #         if groups[0] == '1':
        #             output += separator[1] + ' '
        #         else:
        #             output += f"{groupByHundreds(groups[0], True)}{separator[2]} "

        #     # Millions
        #     elif groupsSize == 3:
        #         # Has millions
        #         if setMillions:
        #             # if not output == "":
        #             separator = literals.millions

        #             if groups[len(groups)-3] == '1':
        #                 output += separator[1] + ' '
        #             else:
        #                 output += f"{groupByHundreds(groups[len(groups)-3], True)}{separator[2]} "
                
        #     # Thousands
        #     elif groupsSize == 2 or groupsSize == 4:
        #         # Has thousands
        #         if not groups[len(groups)-groupsSize] == '000':
        #             setMillions = True

        #             separator = literals.thousands[1]

        #             if groups[len(groups)-groupsSize] == '1' or groups[len(groups)-groupsSize] == '001':
        #                 output += separator + ' '
        #             else:
        #                 output += f"{groupByHundreds(groups[len(groups)-groupsSize], True)}{separator} "
        #         else:
        #             setMillions = False
        #     # Hundreds
        #     elif groupsSize == 1:
        #         output += groupByHundreds(groups[len(groups)-1])
            
        #     groupsSize -= 1

        print(output.capitalize())

        stop = endExec if isTesting else input("Salir? si(s) no(n) ")


# def groupByHundreds(n, isSpecialOne = False):
#         output = ""
#         isTenthOfTwo = isTenthOfOne = hasTens = False

#         digits = len(n) # TODO: Remove initial cero
#         nInt = int(n) # parse n to integer
#         i = digits

#         while i > 0: 
#             # hundreds
#             if i == 3:
#                 output += getHundreds(n, digits)
                
#             # tens
#             elif i == 2:
#                 tens = n[digits-2:]
#                 tensFirstChar = tens[0]

#                 # Has tens
#                 if not tensFirstChar == '0':
#                     hasTens = True

#                     output += getTens(tens, tensFirstChar)

#                     # Special cases 11 - 16
#                     if int(tens) in range(11, 16):
#                         output += ' '
#                         break

#                     # When it's the ten of the 1
#                     if tensFirstChar == '1':
#                         isTenthOfOne = True
#                         output  += 'z ' if int(tens) == 10 else 'ci' # It's number 10

#                     # When it's the ten of the 2
#                     elif tensFirstChar == '2':
#                         isTenthOfTwo = True
#                         output += 'e ' if int(tens) == 20 else 'i' # It's number 20

#                     else:
#                         output  += ' '
                    
#             # units
#             elif i == 1:
#                 nInt = int(n[digits - 1])
#                 unit = literals.units[nInt]
                
#                 # # It's not just zero
#                 # if digits > 1 and nInt == 0:
#                 #     # It's the ten of the 1
#                 #     if isTenthOfOne:
#                 #         output += 'z '

#                 #     # It's the ten of the 2
#                 #     elif isTenthOfTwo:
#                 #         output += 'e '

#                 #     break

#                 # No unit required
#                 if digits > 1 and nInt == 0:
#                     break

#                 # # More tens
#                 # elif 
#                 if hasTens:
#                     if not (isTenthOfOne or isTenthOfTwo):
#                         output += 'y '
#                     # # It's the ten of the 1
#                     # if isTenthOfOne:
#                     #     output += 'ci'

#                     # # It's the ten of the 2
#                     # elif isTenthOfTwo:
#                     #     output += 'i'

#                     # # It's any other ten
#                     # else:
#                     #     output += 'y '

#                     # units when accent is required
#                     if (isTenthOfOne or isTenthOfTwo) and (nInt == 2 or nInt == 3 or nInt == 6):
#                         unit = literals.unitsExceptions[nInt]

#                 # When the text for the 'one' is special
#                 if isSpecialOne and nInt == 1:
#                     unit = literals.unitsExceptions[1]
#                     unit = unit.replace('u', 'ú') if isTenthOfTwo else unit

#                 output += unit + ' '
                
#             i -= 1

#         return output

# def getHundreds(n, digits):
#     output = ""
#     hundreds = n[digits-3:]
#     hFirstChar = hundreds[0]
#     hInt = int(hundreds)

#     # Has hundreds
#     if not hFirstChar == '0':
#         for i in range(1, 10):
#             if int(hFirstChar) == i:
#                 output += literals.hundreds[int(str(i) + '00')]

#                 if int(hFirstChar) == 1 and (hInt in range(101, 200)):
#                     output += 'to'
                
#                 output += ' '
#                 break
        
#     return output
    
# def getTens(tens, tFirstChar):
#     output = ""
#     tens = int(tens)

#     if tens in range(11, 16):
#         output += literals.tens[tens]
#     else:
#         # Loop through 1 - 9
#         for i in range(1, 10):
#             if int(tFirstChar) == i:
#                 output += literals.tens[int(str(i) + '0')]
#                 break

#     return output

if __name__ == '__main__':
    main()