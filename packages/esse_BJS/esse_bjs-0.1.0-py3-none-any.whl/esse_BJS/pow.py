import numpy as np
import spec_err
import sys

def pow(*numbers):
  try:
    if not numbers:
        spec_err.mathy__BJS___NullfuncError()
    
    total = numbers[0]
    for num in numbers[1:]:
        if not isinstance(num, (float, int)):
            spec_err.mathy__BJS___TypeError()
        total = np.power(total, num)
    
    return total
  except OverflowError:
     spec_err.mathy__BJS___OverboundError()
  except Exception as err:
     raise err