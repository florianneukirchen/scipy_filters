import os
import json
import numpy as np

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