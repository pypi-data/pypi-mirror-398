import spec_err
import sys

def add(*numbers):
  try:
    if not numbers:
        spec_err.mathy__BJS___NullfuncError()
    
    total = numbers
    for num in numbers:
        if not isinstance(num, (float, int)):
            spec_err.mathy__BJS___TypeError()
        total += num
    
    return total
  except Exception as err:
     raise err