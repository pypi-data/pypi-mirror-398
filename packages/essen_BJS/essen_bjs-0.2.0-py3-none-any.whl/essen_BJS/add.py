from .spec_err import *
import sys

def add(*numbers):
  try:
    if not numbers:
        mathy__BJS___NullfuncError()
    
    total = numbers
    for num in numbers:
        if not isinstance(num, (float, int)):
          mathy__BJS___TypeError()
        total = sum(total, num)
    
    return total
  except Exception as err:
     raise err