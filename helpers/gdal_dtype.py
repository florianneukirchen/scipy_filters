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

def get_np_dtype(dt_opt):
    return np.dtype(map_dtype[dt_opt])
   
