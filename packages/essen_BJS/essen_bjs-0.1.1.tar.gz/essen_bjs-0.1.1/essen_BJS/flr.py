import spec_err
import sys

def flr(*numbers):
  try:
    if not numbers:
        spec_err.mathy__BJS___NullfuncError()
    
    total = numbers[0]
    for num in numbers[1:]:
        if not isinstance(num, (float, int)):
            spec_err.mathy__BJS___TypeError()
        total //= num
    
    return total
  except ZeroDivisionError:
     spec_err.mathy__BJS___ZerocompatibilityError()
  except Exception as err:
     raise err