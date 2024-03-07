# SciPy filter pack for QGIS
QGIS plugin that gives acces to filters implemented with [SciPy](https://scipy.org/), such as:
- Morphological filters (binary or grey dilation, erosion, closing, opening; tophat etc.)
- Statistical filters (median, minimum etc.)
- Gaussian blur
- Edge detection (sobel, laplace etc.)
- Convolution with a custom kernel

Most filters are based on [scipy.ndimage](https://docs.scipy.org/doc/scipy/reference/ndimage.html),
a libary to filter images (or arrays, rasters) in n dimensions. These 
work either on each layer seperately, or on a 3D datacube of all bands. 
You could also apply a convolution or median filter etc. across the bands for each pixel
by giving the corresponding array as kernel/footprint (note that "bands" is the first axis):

```
[[[1]],
[[1]],
[[1]]]
```

Python users can generate a kernel with numpy and copy the output of str(numpy_array) into the text field. 