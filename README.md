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

```
[[[1]],
[[1]],
[[1]]]
```

Python users can generate a kernel with numpy and copy the relevant part inside the braces of np.array(...) into the text field. The QGIS processing API does not allow to pass numpy arrays directly when calling from the console or a script, but you can convert it to a string using:

```python
str(numpyarray.tolist())
```

Note that these arrays should have the same number of dimensions as the input (2D or 3D). However you can pass a 2D array to a 3D calculation, the plugin automatically adds a new axis as first axis (the result is the same as using the same kernel in 2D).

For more information, see the help in the window of the respective processing tool.

## Requirements for installation
The plugin requires [SciPy](https://scipy.org/), wich can be installed with pip:
```
pip install scipy
```

## Changelog

### Git Main
- Catch exception if SciPy is not installed and offer to install it automatically (with pip)
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

### 0.1 (03/2024)
Initial Release