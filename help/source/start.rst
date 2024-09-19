Getting started
===============

Installation
------------

The plugin can be installed with "manage and install plugins" in QGIS. The plugin requires `SciPy <https://scipy.org/>`_, but the plugin offers to install it (using pip) if it is not already installed.


Usage
-----

The algorithms based on SciPy can be found in the QGIS processing toolbox.

Settings
--------

The plugin settings can be found in the processing section of the QGIS settings. The window size should be large (SciPy is optimized to process large arrays), but not too large (SciPy / QGIS becomes unstable if the data does not fit into the memory). 
The maximum size is only used for algorithms that can't use the windowing function, notably PCA. It only exists to prevent crashes when trying to process very large rasters. 

Tips for Python users
---------------------

As usual, the processing algorithms can be called from the Python console or a script with :code:`processing.run()`.


Kernel / Structure / Footprint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Many filters use a kernel, structure and/or footprint. These are arrays, which have to be entered as string. Python users can generate them with numpy and copy the relevant part inside the braces of `np.array(...)` into the text field. 

The QGIS processing API does not allow to pass numpy arrays directly when calling from the console or a script, but you can convert it to a string using:

.. code-block:: python

    str(numpyarray.tolist())

The order of axes is [bands,] rows, cols. These arrays must have the same number of dimensions as the input (2D or 3D). 
However, if you pass a 2D array to a 3D calculation, the plugin automatically adds a new axis as first axis and the result is the same as using the same kernel in 2D.

Size
~~~~

When calling an algorithm with "size" as parameter from python, you have two options: 

"SIZES": string containing a list of integer values with one value for each axis, such as "1,5,5" or "[3,20,5]" for 3D filters or "5,5" for 2D filters.

"SIZE": integer, use same size for all axes (ignored if SIZES is used).

Dimension, output data type, border mode, etc.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* The integer values are the indices of the combo box.
* In the case of "DTYPE" (output data type), 0 means "same as input data type" and > 0 corresponds to the enum values used by GDAL. Exception: PCA (only float32/float64 as options).

Working in the Python console
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the python console, the class :py:class:`helpers.RasterWizard` helps to get the data of a QGIS raster layer as a numpy array, and the processing result back into QGIS as a new raster layer. It can be used together with :py:class:`helpers.RasterWindow` to process large rasters in a moving window. 