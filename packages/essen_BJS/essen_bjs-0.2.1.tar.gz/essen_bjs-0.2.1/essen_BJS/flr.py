from .spec_err import *
import sys

def flr(*numbers):
  try:
    if not numbers:
        mathy__BJS___NullfuncError()
    
    total = numbers[0]
    for num in numbers[1:]:
        if not isinstance(num, (float, int)):
            mathy__BJS___TypeError()
        total //= num
    
    return total
  except ZeroDivisionError:
     mathy__BJS___ZerocompatibilityError()
  except Exception as err:
     raise err