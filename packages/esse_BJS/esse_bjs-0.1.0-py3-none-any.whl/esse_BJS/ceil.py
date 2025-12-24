import math
import spec_err

def ceil(*numbers):
  try:
    if not numbers:
        spec_err.mathy__BJS___NullfuncError()
    
    total = numbers[0]
    for num in numbers[1:]:
        if not isinstance(num, (float, int)):
            spec_err.mathy__BJS___TypeError()
        total /= num
        total = math.ceil(total)
    
    return total
  except ZeroDivisionError:
     spec_err.mathy__BJS___ZerocompatibilityError()
  except Exception as err:
     raise err