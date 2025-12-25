import numpy as np
from .spec_err import *
import sys

def pow(*numbers):
  try:
    if not numbers:
        mathy__BJS___NullfuncError()
    
    total = numbers[0]
    for num in numbers[1:]:
        if not isinstance(num, (float, int)):
            mathy__BJS___TypeError()
        total = np.power(total, num, dtype=object)
    
    return total
  except OverflowError:
     mathy__BJS___OverboundError()
  except Exception as err:
     raise err