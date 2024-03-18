# SciPy filter pack for QGIS
Experimental QGIS plugin that gives access to [SciPy](https://scipy.org/) filters via the processing toolbox. SciPy offers a range of highly optimised algorithms for i.e. [multidimensional image processing](https://docs.scipy.org/doc/scipy/tutorial/ndimage.html) and [signal processing](https://docs.scipy.org/doc/scipy/tutorial/signal.html), and some can be useful to analyze raster layers.

- QGIS Plugin Repository: [https://plugins.qgis.org/plugins/scipy_filters/](https://plugins.qgis.org/plugins/scipy_filters/)
- Source code: [https://github.com/florianneukirchen/scipy_filters/](https://github.com/florianneukirchen/scipy_filters/)
- Bug tracker: [https://github.com/florianneukirchen/scipy_filters/issues](https://github.com/florianneukirchen/scipy_filters/issues)

## About
Includes raster filters such as:
- Convolution with a custom kernel
- Morphological filters (binary or grey dilation, erosion, closing, opening; tophat etc.)
- Statistical filters (median, minimum, percentile etc.)
- Edge detection (sobel, laplace etc.)


Most filters are based on [scipy.ndimage](https://docs.scipy.org/doc/scipy/reference/ndimage.html), a library to filter images (or arrays, rasters) in n dimensions. For more information, see the SciPy tutorial on [Multidimensional image processing](https://docs.scipy.org/doc/scipy/tutorial/ndimage.html).

These scipy.ndimage filters are either applied on each layer seperately in 2D, or in 3D on a 3D datacube consisting of all bands. 

You could also apply a convolution or median filter etc. across the bands for each pixel
by giving a corresponding array as kernel/footprint/structure (note that "bands" is the first axis), for example:

Python users can generate a kernel with numpy and copy the relevant part inside the braces of np.array(...) into the text field. The QGIS processing API does not allow to pass numpy arrays directly when calling from the console or a script, but you can convert it to a string using:

```python
str(numpyarray.tolist())
```

Note that these arrays should have the same number of dimensions as the input (2D or 3D). However you can pass a 2D array to a 3D calculation, the plugin automatically adds a new axis as first axis (the result is the same as using the same kernel in 2D).

For more information, see the help in the window of the respective processing tool.

## Installation
The plugin can be installed with "manage and install plugins" in QGIS (in the settings of "install plugins", the checkbox "Show also experimental plugins" must be checked.)

The plugin requires [SciPy](https://scipy.org/), wich can be installed with pip:
```
pip install scipy
```
Since version 0.2, the plugin offers an automatic installation of SciPy (using pip) if it is not yet installed in the python environment used by QGIS.

## Changelog

### Git main
- Avoid overflow error in unsharp mask by calculating in float64
- Advanced option to set the dtype of the output (default is dtype of input or float32 for some filters to avoid clipping and overflow errors)
- Convolve: normalize with sum of absolute values of kernel as default, not simply the sum
- Use sizes widget in more filters
- More load options for kernel/structure/footprint
- New origin widget and add origin as parameter to a couple of filters

### 0.2 (03/2024)
- Catch exception if SciPy is not installed and offer to install it automatically (with pip)
- Improved user interface with custom widgets, making it more intuitive and allowing for far better parameters (see breaking changes if you already used version 0.1 in a script or model).
- Calculate and write band statistics (min, max, mean, std) into the metadata of the output file; enables QGIS to render correctly with min/max stretching
- New filters:
    - unsharp mask
    - rank filter
    - uniform  filter (a.k.a. mean filter, box filter)
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