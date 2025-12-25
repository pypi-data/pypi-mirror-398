import math
from .spec_err import *

def ceil(*numbers):
  try:
    if not numbers:
        mathy__BJS___NullfuncError()
    
    total = numbers[0]
    for num in numbers[1:]:
        if not isinstance(num, (float, int)):
            mathy__BJS___TypeError()
        total /= num
        total = math.ceil(total)
    
    return total
  except ZeroDivisionError:
     mathy__BJS___ZerocompatibilityError()
  except Exception as err:
     raise err