import os
import json
import numpy as np
from scipy import ndimage
from qgis.core import QgsProcessingException
from collections import OrderedDict


def str_to_array(s, dims=2, to_int=True):
    s = s.strip()
    if not s:
        return None
    
    if s in ["square", "cross", "cross3D", "ball", "cube"]:
        (rank, connectivity) = generate_binary_structure_options[s]
        a = ndimage.generate_binary_structure(rank, connectivity)
        
    else:
        try:
            decoded = json.loads(s)
            if to_int:
                a = np.array(decoded, dtype="int")
            else:
                a = np.array(decoded, dtype=np.float32)
        except (json.decoder.JSONDecodeError, ValueError, TypeError):
            raise QgsProcessingException('Can not parse string to array!')

    if dims == a.ndim:
        return a
    if a.ndim == 2 and dims == 3:
        a = a[np.newaxis,:]
        return a
    raise QgsProcessingException('Array has wrong number of dimensions!')


generate_binary_structure_options = {
    "square": (2, 2), 
    "cross": (2, 1), 
    "cross3D": (3, 1), 
    "ball": (3,2), 
    "cube": (3,3), 
}

def check_structure(s, dims=2, odd=False, optional=True):
    s = s.strip()
    if optional and not s:
        return (True, "")
    if s == "" and not optional:
        return (False, "Argument is not optional")
    if s in ["square", "cross"]:
        return (True, "")
    if s in ["cross3D", "ball", "cube"]:
        if dims == 3:
            return(True, "")
        else:
            return (False, f'{s} not possible in 2D')

    # Get it as array
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






footprintexamples = OrderedDict([
    ("3 × 3 Square", np.ones((3,3))),
    ("5 × 5 Square", np.ones((5,5))),

])


kernelexamples = OrderedDict([
    ("3 × 3 Gaussian", "[[1, 2, 1],\n[2, 4, 2],\n[1, 2, 1]]"),
    ("3 × 3 Square", np.ones((3,3))),
    ("5 × 5 Square", np.ones((5,5))),

])