# SciPy Filters for QGIS
QGIS plugin providing access to [SciPy](https://scipy.org/) filters via the processing toolbox. SciPy offers a range of highly optimised algorithms for i.e. [multidimensional image processing](https://docs.scipy.org/doc/scipy/tutorial/ndimage.html) and [signal processing](https://docs.scipy.org/doc/scipy/tutorial/signal.html), and some can be useful to analyze raster layers.

Includes raster filters such as:
- Convolution with a custom kernel (classic or with FFT)
- Morphological filters (binary/grey dilation, erosion, closing, opening; tophat etc.)
- Principal Component Analysis (PCA)
- Statistical filters (local median, minimum, percentile etc.)
- Edge detection (sobel, laplace etc.)
- Unsharp mask for sharpening, Wiener filter for noise reduction
- Pixel statistics (std, mean, min ... of all bands for individual pixels)


Most filters are based on [scipy.ndimage](https://docs.scipy.org/doc/scipy/reference/ndimage.html), a library to filter images (or arrays, rasters) in *n* dimensions. These are either applied on each layer seperately in 2D, or in 3D on a 3D datacube consisting of all bands.  For more information, see the SciPy tutorial on [Multidimensional image processing](https://docs.scipy.org/doc/scipy/tutorial/ndimage.html). In most cases, the plugin simply provides a user interface for a single SciPy function, gets the raster data using GDAL, calls the SciPy function with the provided parameters and loads the result back into QGIS. A few filters (PCA, unsharp mask, pixel statistics etc.) use custom functions that where implemented using SciPy and/or Numpy. Very large rasters are processed using a moving window (i.e. in tiles).

For many filters, a custom footprint and/or structure or kernel can be provided, adjusting the size and shape of the filter. 

For more information, see [https://florianneukirchen.github.io/scipy_filters/](https://florianneukirchen.github.io/scipy_filters/) or the help in the window of the respective processing tool.

Python users get `helpers.RasterWizard` to quickly get the data of a raster layer as numpy array and the processing result back into QGIS as a new raster layer. 

## Resources
- QGIS Plugin Repository: [https://plugins.qgis.org/plugins/scipy_filters/](https://plugins.qgis.org/plugins/scipy_filters/)
- Source code: [https://github.com/florianneukirchen/scipy_filters/](https://github.com/florianneukirchen/scipy_filters/)
- Bug tracker: [https://github.com/florianneukirchen/scipy_filters/issues](https://github.com/florianneukirchen/scipy_filters/issues)
- Documentation: [https://florianneukirchen.github.io/scipy_filters/](https://florianneukirchen.github.io/scipy_filters/)



## Installation
The plugin can be installed with "manage and install plugins" in QGIS. Eventually, in the settings of "install plugins", the checkbox "Show also experimental plugins" must be checked.

The plugin requires [SciPy](https://scipy.org/), which can be installed with pip:
```
pip install scipy
```
Since version 0.2, the plugin offers an automatic installation of SciPy (using pip) if it is not yet installed in the python environment used by QGIS.

## Settings
The plugin settings can be found in the processing section of the QGIS settings. The window size should be large (SciPy is optimized to process large arrays), but not too large (SciPy / QGIS becomes unstable if the data does not fit into the memory). 
The maximum size is only used for algorithms that can't use the windowing function, notably PCA. It only exists to prevent crashes when trying to process very large rasters. 

## No data cells
Since most filters work within a neighborhood, it is not enough to mask no data values: A no data pixel in the neighborhood would keep the no data value of the file (e.g. -9999) while applying the filter, drastically changing the result. 

As a work around, the plugin fills no data cells either with 0 (most cases), with the band mean or with the smallest or largest possible value of the data type (see help of each filter for details).

To fine tune the behavior, it is possible to use the filters of the no data group: Get a no data mask, fill no data values with a suitable value, apply the filter, apply the no data mask to set no data cells back to no data. 

Also note that no data values at the edge of the raster (typically caused by reprojecting to another CRS) interfere with the border modes available in some scipy.ndimage filters such as "reflect", "nearest", "mirror", "wrap": no data cells will be reflected, mirrored, wrapped as well. 


## Tips for python users

### Kernel / Structure / Footprint
Many filters use a kernel, structure and/or footprint. These are arrays, which have to be entered as string. Python users can generate them with numpy and copy the relevant part inside the braces of `np.array(...)` into the text field. The QGIS processing API does not allow to pass numpy arrays directly when calling from the console or a script, but you can convert it to a string using:

```python
str(numpyarray.tolist())
```
(Note: str(numpyarray) does not work, the colons are missing in the resulting string.)

The order of axes is `[bands,] rows, cols`. These arrays must have the same number of dimensions as the input (2D or 3D). However, if you pass a 2D array to a 3D calculation, the plugin automatically adds a new axis as first axis and the result is the same as using the same kernel in 2D.

### Size
When calling an algorithm with "size" as parameter from python, you have two options: 
- `"SIZES"`: string containing a list of integer values with one value for each axis, such as `"1,5,5"` or `"[3,20,5]"` for 3D filters or `"5,5"` for 2D filters.
- `"SIZE"`: integer, use same size for all axes (ignored if SIZES is used).

### Dimension, output data type, border mode, etc.
- The integer values are the indices of the combo box.
- In the case of `"DTYPE"` (output data type), 0 means "same as input data type" and > 0 corresponds to the enum values used by [gdal](https://gdal.org/index.html). Exception: PCA (only float32/float64 as options).

### RasterWizard
In the QGIS python console, `RasterWizard` allows to quickly get the data of a raster layer as a numpy array, and the processing result back into QGIS as a new raster layer. This allows for processing with [NumPy](https://numpy.org/), [SciPy](https://scipy.org/), [scikit-image](https://scikit-image.org/), 
[scikit-learn](https://scikit-learn.org/stable/) or other python libraries. Great for prototype development and experimenting with algorithms.

See the [API documentation of RasterWizard](https://florianneukirchen.github.io/scipy_filters/wizard.html) for more information.

(New in version 1.3)

Example:
```python
from scipy_filters.helpers import RasterWizard
from scipy import ndimage

wizard = RasterWizard() # Uses active layer if layer is not given
a = wizard.toarray()    # Returns numpy array with all bands

# Any calculation, for example a sobel filter with Scipy
# In the example, the result is a numpy array with dtype float32
b = ndimage.sobel(a, output="float32") 

# Write the result to a geotiff and load it back into QGIS
wizard.tolayer(b, name="Sobel", filename="/path/to/sobel.tif")
```

Getting more info about the raster:
```python
# You can also get pixel values at [x, y]
wizard[0,10] 

# or information like shape, CRS, etc.
wizard.shape   # like numpy_array.shape
wizard.crs_wkt # CRS as WKT string
wizard.crs     # CRS as QgsCoordinateReferenceSystem
```

## Changelog

### Git
- Check if layer is provided by gdal (i.e. local file, not wms etc.) and give feedback if otherwise (RasterWizard raises TypeError). 
- RasterWizard: Support setting band descriptions and accessing bands by band description.
### 1.4 (09/2024)
- RasterWizard: Raise TypeError if layer is not a QgsRasterLayer
### 1.3 (09/2024)
- Add helpers.RasterWizard
- generate help
### 1.2 (04/2024)
- Bugfix: PCA, calculate band mean without no data value
### 1.1 (04/2024)
- Mask no data cells (no data pixels remain no data pixels)
- Fill no data cells to smooth the leaking into the neighborhood
- Add filter to calculate a no data mask
- Add filter to apply a no data mask (set corresponding cells to no data)
- Add filter to fill no data cells of all bands with either 0, a given value, the band mean, the minimum value of the data type, the maximum value of the data type or the central value of the data type 
### 1.0 (04/2024)
- For large rasters: calculate in a moving window to avoid crashes
- Add setValue() to the custom widgets to get loading from history working
- Calculating band statistics after completion is optional now
- Get translation working (except for help strings)
- Add German translation
- New algorithms: 
    - correlate with a given kernel (classic and FFT versions)
    - gradient (x,y axes and for pixels across bands)
    - difference (each pixel across bands) 
    - keep only n components of PCA

### 0.3 (03/2024)
- New: Principal Component Analysis (PCA)
- Advanced option to change the dtype of the output 
- For filters where negative values are expected in the output, use float32 as default output dtype (instead of dtype of input layer) to avoid clipping and overflow errors 
- Convolve: normalize with sum of absolute values of kernel as default, not simply the sum
- Unsharp mask: Avoid overflow error by calculating in float64
- Use sizes widget in more filters
- More load options for kernel/structure/footprint
- New origin widget and add origin as parameter to a couple of filters
- New set of filters for pixel statistics (std, mean, min ... of all bands for individual pixels)

### 0.2 (03/2024)
- Catch exception if SciPy is not installed and offer to install it automatically (with pip)
- Improved user interface with custom widgets, making it more intuitive and allowing for far better parameters (see breaking changes if you already used version 0.1 in a script or model).
- Calculate and write band statistics (min, max, mean, std) into the metadata of the output file; enables QGIS to render correctly with min/max stretching
- New filters:
    - unsharp mask
    - rank filter
    - uniform filter (a.k.a. mean filter, box filter)
    - estimate local variance
    - estimate local standard deviation
    - range filter 
    - fourier gaussian filter
    - fourier ellipsoid filter
    - fourier uniform filter
    - Wiener filter
    - FFT convolve
- Breaking changes to the parameters:
    - FOOTPRINTBOOL has been removed, if a footprint is given it is always used.
    - STRUCTURE always takes the actual structure as string (as CUSTOMSTRUCTURE in version 0.1), not an int (was index of combobox, the combobox has been replaced by the load button). CUSTOMSTRUCTURE has been removed.
    - Convolve: ORIGIN has been removed. (An improved version is on the todo list)

### 0.1 (03/2024)
Initial Release