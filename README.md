# SciPy filter pack for QGIS
Experimental QGIS plugin that gives access to [SciPy](https://scipy.org/) filters via the processing toolbox.

- Source code: [https://github.com/florianneukirchen/scipy_filters/](https://github.com/florianneukirchen/scipy_filters/)
- Bug tracker: [https://github.com/florianneukirchen/scipy_filters/issues](https://github.com/florianneukirchen/scipy_filters/issues)

## About
Includes raster filters such as:
- Morphological filters (binary or grey dilation, erosion, closing, opening; tophat etc.)
- Statistical filters (median, minimum, percentile etc.)
- Gaussian blur
- Edge detection (sobel, laplace etc.)
- Convolution with a custom kernel

Most filters are based on [scipy.ndimage](https://docs.scipy.org/doc/scipy/reference/ndimage.html), a library to filter images (or arrays, rasters) in n dimensions. For more information, see the SciPy tutorial on [Multidimensional image processing](https://docs.scipy.org/doc/scipy/tutorial/ndimage.html).

These scipy.ndimage filters are either applied on each layer seperately in 2D, or in 3D on a 3D datacube consisting of all bands. 

You could also apply a convolution or median filter etc. across the bands for each pixel
by giving a corresponding array as kernel/footprint/structure (note that "bands" is the first axis), for example:

```
[[[1]],
[[1]],
[[1]]]
```

Python users can generate a kernel with numpy and copy the output of str(numpy_array) into the text field. Note that these arrays should have the same number of dimensions as the input (2D or 3D). However you can pass a 2D array to a 3D calculation, the plugin automatically adds a new axis as first axis (the result is the same as using the same kernel in 2D).

For more information, see the help in the window of the respective processing tool.

## Requirements for installation
The plugin requires [SciPy](https://scipy.org/), wich can be installed with pip:
```
pip install scipy
```

## Changelog

### Git Main
- Catch exception if SciPy is not installed and offer to install it automatically (with pip)
- finish and enable rank filter

### 0.1 (03/2024)
Initial Release