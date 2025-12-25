import math
from .spec_err import *

def roundi(number):
  try:
    if not number:
        mathy__BJS___NullfuncError()
    
    if not isinstance(number, (float, int)):
       mathy__BJS___TypeError()
    
    total = round(number)
    return total
  except Exception as err:
     raise err