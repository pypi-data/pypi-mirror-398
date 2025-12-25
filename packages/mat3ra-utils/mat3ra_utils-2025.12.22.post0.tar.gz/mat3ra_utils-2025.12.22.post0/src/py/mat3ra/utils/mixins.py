import numpy as np


class RoundNumericValuesMixin(object):
    # Default rounding precision in decimal places
    __round_precision__ = 9

    @classmethod
    def round_array_or_number(cls, array, decimal_places=None, retain_sign_for_zero=False):
        decimal_places = cls.__round_precision__ if decimal_places is None else decimal_places
        rounded_array = np.round(array, decimal_places)
        resulting_ndarray = rounded_array
        if not retain_sign_for_zero:
            resulting_ndarray = np.where(rounded_array == 0, 0.0, rounded_array)
        return resulting_ndarray.tolist()
