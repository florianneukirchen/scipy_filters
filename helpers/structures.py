"""
/***************************************************************************
 SciPyFilters
                                 A QGIS plugin
 Filter collection implemented with SciPy
                              -------------------
        begin                : 2024-03-03
        copyright            : (C) 2024 by Florian Neukirchen
        email                : mail@riannek.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""


import json
import numpy as np
from scipy import ndimage
from qgis.core import QgsProcessingException
from collections import OrderedDict

from .i18n import tr

def str_to_array(s, dims=2, to_int=True):
    """Turn string of kernel/footprint/structure to numpy array

    String should be a list of lists, e.g. [[1,2,3],[4,5,6],[7,8,9]]
    or a code such as "square", "cross", "cross3D", "ball", "cube".

    :param s: string to be converted
    :param dims: number of dimensions of the array, 2 or 3
    :param to_int: if True, dtype of array must be int
    :return: numpy array
    """
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

    if dims == None:
        return a

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
    """
    Check if structure is valid 
    
    A valid structure can be converted with str_to_array().
    Returns tuple: (ok: bool, message: str, shape: tuple | None)
    Shape is required for origin

    :param s: string to be converted
    :param dims: number of dimensions of the array, 2 or 3
    :param odd: if True, all values must be odd (for Wiener filter)
    :param optional: if True, empty string is allowed and returns True
    :return: tuple: (ok: bool, message: str, shape: tuple | None)
    """
    s = s.strip()
    if optional and not s:
        if dims == 2:
            return (True, "", (0,0))
        else:
            return (True, "", (0,0,0))
    if s == "" and not optional:
        return (False, tr("Argument is not optional"), None)
    if s in ["square", "cross"]:
        return (True, "", (3,3))
    if s in ["cross3D", "ball", "cube"]:
        if dims == 3:
            return(True, "", (3, 3, 3))
        else:
            return (False, tr('{} not possible in 2D').format(s), None)

    # Get it as array
    try:
        decoded = json.loads(s)
        a = np.array(decoded, dtype=np.float32)
    except (json.decoder.JSONDecodeError, ValueError, TypeError):
        return (False, tr('Invalid input'), None)

    # Array must have same number of dims as the filter input,
    # but for 3D input and 2D structure I automatically add one axis
    if not (a.ndim == 2 or a.ndim == dims):
        return (False, tr('Array has wrong number of dimensions'), None)

    # Wiener filter: values must be odd
    if odd and np.any(a % 2 == 0):
        return (False, tr('Every element in size must be odd.'), None)
    
    if a.ndim == 2 and dims == 3:
        a = a[np.newaxis,:]

    return (True, "", a.shape)


def check_origin(s, shape):
    msg =  tr('Invalid origin')
    try:
        int_or_list = str_to_int_or_list(s)
    except ValueError:
        return (False, msg)
    
    if isinstance(int_or_list, int):
        if (-(min(shape) // 2) <= int_or_list <= (min(shape) -1 ) // 2):
            return (True, "")
        else:
            return (False, msg)
    
    if not len(shape) == len(int_or_list):
        return (False, msg)

    for i in range(len(shape)):
        # origin must satisfy -(weights.shape[k] // 2) <= origin[k] <= (weights.shape[k]-1) // 2
        if not (-(shape[i] // 2) <= int_or_list[i] <= (shape[i] - 1) // 2):
            return (False, msg)

    return (True, '')



def str_to_int_or_list(s):
    """Parse string to int or list of ints

    String should be a list of integers, e.g. [1,2,3], optionally without brackets;
    or a single integer.

    Used to have parameters for axes (one or several) or size (for all or each dimension)

    :param s: string to be converted
    :return: int or list of ints
    """
    if s == "0":
        return 0
    out = None
    s = s.strip()
    try:
        out = int(s)
    except ValueError:
        pass
    if out:
        return out
    if s == "":
        return None
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
    """Convert numpy array to string
    
    For pretty printing of arrays, line breaks are added.
    :param a: numpy array
    :return: string
    """
    s = str(a.tolist())
    s = s.replace('], [', '],\n[')
    return s




footprintexamples = OrderedDict([
    (tr("3 × 3 Square"), np.ones((3,3))),
    (tr("5 × 5 Square"), np.ones((5,5))),
    (tr("7 × 7 Square"), np.ones((7,7))),
    (tr("Cross"), ndimage.generate_binary_structure(2, 1)),
    ("sep1", "---"), 
    (tr("3 × 3 × 3 Cube"), np.ones((3,3,3))),
    (tr("5 × 5 × 5 Cube"), np.ones((5,5,5))),
    (tr("7 × 7 × 7 Cube"), np.ones((7,7,7))),
])


kernelexamples = OrderedDict([
    (tr("3 × 3 Square"), np.ones((3,3))),
    (tr("5 × 5 Square"), np.ones((5,5))),
    (tr("7 × 7 Square"), np.ones((7,7))),
    (tr("Cross 2D"), ndimage.generate_binary_structure(2, 1).astype(float)),
    ("sep1", "---"), 
    (tr("3 × 3 Gaussian"), "[[1, 2, 1],\n[2, 4, 2],\n[1, 2, 1]]"),
    (tr("5 × 5 Gaussian"), "[[0,1,2,1,0],\n[1,3,5,3,1],\n[2,5,9,5,2],\n[1,3,5,3,1],\n[0,1,2,1,0]]"),
    (tr("5 × 5 Laplacian of Gaussian"), "[[0,0,-1,0,0],\n[0,-1,-2,-1,0],\n[-1,-2,16,-2,-1],\n[0,-1,-2,-1,0],\n[0,0,-1,0,0]]"),
    (tr("3 × 3 Sobel horizontal edges"), "[[1, 2, 1],\n[0, 0, 0],\n[-1, -2, -1]]"),
    (tr("3 × 3 Sobel vertical edges"), "[[1, 0, -1],\n[2, 0, -2],\n[1, 0, -1]]"),
    ("sep2", "---"), 
    (tr("3 × 3 × 3 Cube"), np.ones((3,3,3))),
    (tr("5 × 5 × 5 Cube"), np.ones((5,5,5))),
    (tr("7 × 7 × 7 Cube"), np.ones((7,7,7))),
    (tr("Cross 3D"), ndimage.generate_binary_structure(3, 1).astype(float)),
    (tr("Ball 3D"), ndimage.generate_binary_structure(3, 2).astype(float)),
    (tr("Cube 3D"), ndimage.generate_binary_structure(3, 3).astype(float)),
    (tr("3 × 1 × 1 Across bands of pixel"), np.ones((3,1,1)))
])

morphostructexamples =  OrderedDict([
    (tr("Cross 2D"), ndimage.generate_binary_structure(2, 1)),
    (tr("Square 2D"), ndimage.generate_binary_structure(2, 2)),
    ("sep1", "---"), 
    (tr("Cross 3D"), ndimage.generate_binary_structure(3, 1)),
    (tr("Ball 3D"), ndimage.generate_binary_structure(3, 2)),
    (tr("Cube 3D"), ndimage.generate_binary_structure(3, 3)),
    ("sep1", "---"), 
    (tr("5 × 5 Square"), np.ones((5,5))),
    (tr("7 × 7 Square"), np.ones((7,7))),
    (tr("5 × 5 × 5 Cube"), np.ones((5,5,5))),
])