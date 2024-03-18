import numpy as np

dtype_options = ['Same as input', 
                 'Byte (unsigned 8 bit integer)',
                 'UInt16 (unsigned 16 bit integer)',
                 'Int16 (signed 16 bit integer)',
                 'UInt32 (unsigned 32 bit integer)',
                 'Int32 (signed 32 bit integer)',
                 'Float32 (32 bit float)',
                 'Float64 (64 bit float)',]

map_dtype = {
        1: "uint8",
        2: "uint16",
        3: "int16",
        4: "uint32",
        5: "int32",
        6: "float32",
        7: "float64",
}

def convert_dtype(a, dt_opt, feedback, band=None):
    if band:
        bands = f"Band {band}: "
    else:
        bands=""
    feedback.pushInfo("{band}Convert input dataset to {dtype_options[dt_opt]}")
    new_dtype = np.dtype(map_dtype[dt_opt])
    # Clip values if integer
    if np.issubdtype(new_dtype, np.integer):
        info = np.iinfo(new_dtype)
        if a.min() < info.min or a.max() > info.max:
            err = f"{band}Warning: input values are out of bound of new dtype, clipping input to {info.min}...{info.max}"
            feedback.reportError(err, fatalError = False)

        a = np.clip(a, info.min, info.max)
    
    return a.astype(new_dtype)
    
