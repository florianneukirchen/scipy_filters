import os
import json
import numpy as np
from qgis.core import QgsProcessingException


def str_to_array(s, dims=2, to_int=False):
    try:
        decoded = json.loads(s)
        if to_int:
            a = np.array(decoded, dtype="int")
        else:
            a = np.array(decoded, dtype=np.float32)
    except (json.decoder.JSONDecodeError, ValueError, TypeError):
        raise QgsProcessingException('Can not parse string to array!')

    # Array must have same number of dims as the filter input,
    # but for 3D input and 2D structure I automatically add one axis
    # When getting the parameter, self._dimension is already set
    # but in checkParameters we need to pass them to this function

    # if not dims:
    #     dims = 2 
    #     if self._dimension == self.Dimensions.threeD:
    #         dims = 3
    # TODO remove

    if dims == a.ndim:
        return a
    if a.ndim == 2 and dims == 3:
        a = a[np.newaxis,:]
        return a
    raise QgsProcessingException('Array has wrong number of dimensions!')


def check_structure(s, dims=2, odd=False, optional=True):
    if optional and not s:
        return (True, "")
    try:
        decoded = json.loads(s)
        a = np.array(decoded, dtype=np.float32)
    except (json.decoder.JSONDecodeError, ValueError, TypeError):
        return (False, 'Can not parse string to array')

    # Array must have same number of dims as the filter input,
    # but for 3D input and 2D structure I automatically add one axis
    if not (a.ndim == 2 or a.ndim == dims):
        return (False, 'Array has wrong number of dimensions')

    # Wiener filter: values must be odd
    if odd and np.any(a % 2 == 0):
        return (False, 'Every element in size must be odd.')

    return (True, "")


def str_to_int_or_list(s):
    """
    Allow to have parameters for axes (one or several) or size (for all or each dimension)
    """
    out = None
    try:
        out = int(s)
    except ValueError:
        pass
    if out:
        return out
    
    if not (s[0] == "[" and s[-1] == "]"):
        s = "[" + s + "]"

    try:
        decoded = json.loads(s)
        a = np.array(decoded, dtype=np.int32)
    except (json.decoder.JSONDecodeError, ValueError, TypeError):
        raise ValueError('Can not parse string to array!')
    
    if a.ndim != 1:
        raise ValueError('Wrong dimensions!')
    
    return a.tolist()



def array_to_str(a):
    s = str(a.tolist())
    s = s.replace('], [', '],\n[')
    return s