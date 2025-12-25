import math
import spec_err

def roundi(number):
  try:
    if not number:
        spec_err.mathy__BJS___NullfuncError()
    
    if not isinstance(number, (float, int)):
       spec_err.mathy__BJS___TypeError()
    
    total = round(number)
    return total
  except Exception as err:
     raise err