# -*- coding: utf-8 -*-

"""
/***************************************************************************
 SciPyFilters
                                 A QGIS plugin
 Filter collection implemented with SciPy
                              -------------------
        begin                : 2024-03-26
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

__author__ = 'Florian Neukirchen'
__date__ = '2024-03-26'
__copyright__ = '(C) 2024 by Florian Neukirchen'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import numpy as np

DEFAULTWINDOWSIZE = 5000 # Large is faster, but must be small enought for RAM
MAXSIZE = 200 # Max size in Mpixels for algs that can't use a window 

class RasterWindow():
    """
    Window for reading/writing a subset of a raster into/from a numpy array.

    Helper class for a window (tile) of a large raster to be used for processing
    in a moving window. The window can have a margin, for algorithms that consider
    the neighborhood of a pixel as well. For example, a 3x3 kernel needs a margin of 1.

    The windows (RasterWindow instances) can be generated with :py:func:`.get_windows`.
     
    Does not contain any data, only the parameters to read/write a subset of the raster with `GDAL <https://gdal.org/en/latest/>`_
    and to slice off the margin before writing data to the output dataset.
    
    To read and write the data with `GDAL <https://gdal.org/en/latest/>`_ use the :py:attr:`.gdalin` 
    and :py:attr:`.gdalout` properties. Any margin must be removed from the numpy array before writing
    the data back to the raster, see :py:meth:`.getslice`.

    Example::

        # Input and output datasets with gdal
        ds = gdal.Open("raster.tif") 
        driver = gdal.GetDriverByName("GTiff")
        dst_ds = driver.CreateCopy(dst_filename, src_ds, strict=0)

        # Get windows
        windows = get_windows(ds.RasterXSize, ds.RasterYSize, windowsize=windowsize, margin=margin)

        # Loop over windows
        band = 1
        for win in windows:
            a = ds.GetRasterBand(band).ReadAsArray(*win.gdalin) # In this case a is a 2D numpy array
            # Your calculation with numpy array a
            a = a[win.getslice(2)] # Slice off the margin (2D array)
            dst_ds.GetRasterBand(band).WriteArray(filtered, *win.gdalout)

        # Close datasets (flushes data to file)
        ds = None
        dst_ds = None

    """
    def __init__(self, rasterXSize, rasterYSize, xoff, yoff, xsize, ysize, margin=0):
        self.rasterXSize = rasterXSize
        self.rasterYSize = rasterYSize

        # Without margin
        self.xoff = xoff
        self.yoff = yoff
        self.xsize = xsize
        self.ysize = ysize
        self.xshift = 0
        self.yshift = 0
        self.margin = margin


        # With margin
        self.m_xsize = self.xsize + 2 * self.margin
        self.m_ysize = self.ysize + 2 * self.margin

        self.m_xoff = self.xoff - self.margin
        self.m_yoff = self.yoff - self.margin


        # Shift the window if on edge
        if self.m_xoff < 0:
            self.xshift = self.margin
            self.m_xoff = 0
    
        if self.m_yoff < 0:
            self.yshift = self.margin
            self.m_yoff = 0

        if self.m_xoff + self.m_xsize > self.rasterXSize:
            self.xshift = -self.margin
            self.m_xoff = self.rasterXSize - self.m_xsize
    
        if self.m_yoff + self.m_ysize > self.rasterYSize:
            self.yshift = -self.margin
            self.m_yoff = self.rasterYSize - self.m_ysize


    @property
    def gdalin(self):
        """
        Parameters for `GDAL <https://gdal.org/en/latest/>`_ ReadAsArray() method.

        Tuple with x_offset, y_offset, x_size, y_size (including the margins of the window). 
        The tuple can be unpacked with * to be used as parameters with ReadAsArray.

        Example::

            a = ds.GetRasterBand(band).ReadAsArray(*win.gdalin)

        :return: tuple with x_offset, y_offset, x_size, y_size 
        """
        return self.m_xoff, self.m_yoff, self.m_xsize, self.m_ysize
    
    @property
    def gdalout(self):
        """
        Parameters for `GDAL <https://gdal.org/en/latest/>`_ WriteArray() method.

        Tuple with x_offset, y_offset (excluding the margins of the window).
        The tuple can be unpacked with * to be used as parameters with the `GDAL <https://gdal.org/en/latest/>`_ 
        WriteArray() method.
        Margins must from the numpy array before writing to the output dataset, see :py:meth:`.get_slice`.

        Example::

            a = a[win.getslice()] # Slice off the margin
            dst_ds.WriteArray(a, *win.gdalout)

        :return: tuple with x_offset, y_offset
        """
        return self.xoff, self.yoff
    
    # Only for debugging:
    @property
    def gdalin_no_margin(self):
        """
        Parameters for `GDAL <https://gdal.org/en/latest/>`_ ReadAsArray() method to read data without margin.

        Only for debugging, use :py:attr:`.gdalin` instead.

        :return: tuple with x_offset, y_offset, x_size, y_size including the margins 
        """
        return self.xoff, self.yoff, self.xsize, self.ysize
    
    def getslice(self, ndim=3):
        """
        Get tuple of :py:obj:`slice` objects to be used directly with numpy to remove the margin of the window
        before writing the data into the output dataset.

        Example::
            
                a = a[win.getslice()] # Slice off the margin of a 3D numpy array

        :param ndim: number of dimensions of the numpy array; either 2 or 3, default is 3
        :type ndim: int, optional
        :return: tuple of slice objects
        """
        ystop = -(self.margin + self.yshift)
        xstop = -(self.margin + self.xshift)

        if ystop == 0: ystop = None
        if xstop == 0: xstop = None


        ys = slice(self.margin - self.yshift, ystop, None)
        xs = slice(self.margin - self.xshift, xstop, None)
        if ndim == 2:
            return (ys, xs) 
        else:
            return (slice(None, None, None), ys, xs)
    
    def __str__(self):
        return f"<RasterWindow>{self.xoff} {self.yoff} size {self.xsize} {self.ysize} margin {self.margin}"

    def get_a_off(self):
        """
        Get the x and y offsets with and without margins.

        Primarily for debugging.

        :return: tuple with x_offset, y_offset, x_offset_no_margin, y_offset_no_margin
        """
        return self.xoff, self.yoff, self.m_xoff, self.m_yoff



def get_windows(rasterXSize, rasterYSize, windowsize=5000, margin=0):
    """
    Generator yielding :py:class:`RasterWindow` instances, dividing a large raster into smaller
    windows (tiles).

    The generated window objects do not contain the data, 
    only the pixel indices and sizes that are used internally to read and write the data 
    with `GDAL <https://gdal.org/en/latest/>`_.

    Note that numpy, scipy etc. are very performant on large arrays. It is best to use a 
    large windowsize or even the whole raster, as long as enough memory is avaible.
    The windows can have a margin, for algorthims that consider the neighborhood of a pixel as well.
    For example, a 3x3 kernel needs a margin of 1.

    If you need the number of windows (e.g. for a progress bar), use :py:func:`.number_of_windows`.

    :param rasterXSize: number of pixels in x direction of the raster
    :type rasterXSize: int
    :param rasterYSize: int, number of pixels in y direction of the raster
    :type rasterYSize: int
    :param windowsize: Size of the windows in x and y direction in pixels, default is 5000
    :type windowsize: int, optional
    :param margin: Size of the margin in pixels, default is 0
    :type margin: int, optional

    :return: :py:class:`RasterWindow` instances
    """
    if windowsize == None:
        # get 1 window with full raster 
        yield RasterWindow(rasterXSize, rasterYSize, 0, 0, rasterXSize, rasterYSize, margin=0)
        return

    if (np.min((rasterXSize, rasterYSize))  < 2 * windowsize):
        # print("only one")
        # get 1 window with full raster 
        yield RasterWindow(rasterXSize, rasterYSize, 0, 0, rasterXSize, rasterYSize, margin=0)
        return
    
    for x in range(0, rasterXSize, windowsize):

        if x + 1.5 * windowsize > rasterXSize:
            xsize = rasterXSize - x 
        else:
            xsize = windowsize

        for y in range(0, rasterYSize, windowsize):

            if y + 1.5 * windowsize > rasterYSize:
                ysize = rasterYSize - y 
            else:
                ysize = windowsize
                
            if (xsize > windowsize / 2) and (ysize > windowsize / 2):
                yield RasterWindow(rasterXSize, rasterYSize, x, y, xsize, ysize, margin)


def number_of_windows(rasterXSize, rasterYSize, windowsize):
    """
    Returns the number of windows that would be created with :py:func:`.get_windows`. 
    
    To be used for progress bar, etc.

    :param rasterXSize: number of pixels in x direction of the raster
    :type rasterXSize: int
    :param rasterYSize: number of pixels in y direction of the raster
    :type rasterYSize: int
    :param windowsize: Size of the windows in x and y direction in pixels
    :type windowsize: int
    :return: int, number of windows
    """
    if windowsize == None:
        return 1
    if (np.min((rasterXSize, rasterYSize))  < 2 * windowsize):
        return 1
    x = np.ceil(rasterXSize / windowsize)
    y = np.ceil(rasterYSize / windowsize)
    if (rasterXSize % windowsize) < (windowsize / 2):
        x = x - 1
    if (rasterYSize % windowsize) < (windowsize / 2):
        y = y - 1
    return int(x * y)
    

def wrap_margin(a, dataset, win: RasterWindow, band=None):
    """
    Fill margin of numpy array to enable SciPy filters with mode wrap.

    Fills the margin of a numpy array that was read from a :py:class:`RasterWindow` that is situated on the edge
    of the original raster with the data of the far side of the raster.
    This makes :code:`mode="wrap"`, offered by some `SciPy <https://scipy.org/>`_ filters, possible.
    The wrapping itself is done by SciPy, this function only fills the
    data needed for wrapping to work.

    
    Example::

        import gdal
        from scipy import ndimage
        from scipy_filters.helpers.window import get_windows, wrap_margin

        ds = gdal.Open("raster.tif") 
        driver = gdal.GetDriverByName("GTiff")
        dst_ds = driver.CreateCopy(dst_filename, src_ds, strict=0)

        windows = get_windows(ds.RasterXSize, ds.RasterYSize, windowsize=2000, margin=2)

        for band in range(1, ds.RasterCount + 1):
            for win in windows:
                a = ds.GetRasterBand(band).ReadAsArray(*win.gdalin) 
                wrap_margin(a, ds, win, band=band)
                # Your calculation, for example median filter
                a = ndimage.median_filter(a, size=5, mode="wrap")
                a = a[win.getslice(2)] # Slice off the margin of the 2D array
                dst_ds.GetRasterBand(band).WriteArray(filtered, *win.gdalout)

    :param a: Numpy array with the data of the window
    :param dataset: gdal dataset of the input raster
    :param win: RasterWindow
    :param band: int | None. Number of band (and using a 2D array), None for all bands (3D array if more than 1 band exists).
    """
    rasterXSize = dataset.RasterXSize
    rasterYSize = dataset.RasterYSize
    # Shortcut: Nothing to do if we are not on edge
    if win.xshift == win.yshift == 0:
        return
    
    # No wrapping needed if window is full raster
    if win.xsize == win.rasterXSize:
        return
    
    # If band, get the array of the band, otherwise of the complete ds
    if band:
        dataset = dataset.GetRasterBand(band)

    # Prepare slices (for tile array) and offsets (for full dataset)
        
    n_slice = slice(None, None)

    # Small sides
    if win.xshift > 0:
        x_slice = slice(-win.margin, None)
        xoff = rasterXSize - win.margin
    else:
        x_slice = slice(0, win.margin)
        xoff = 0

    if win.yshift > 0:
        y_slice = slice(-win.margin, None)
        yoff = rasterYSize - win.margin
    else:
        y_slice = slice(0, win.margin)
        yoff = 0

    # Long sides
    x_long_slice = slice(0, win.m_xsize)
    y_long_slice = slice(0, win.m_ysize)

    # Do the wrapping
        
    # left or right side    
    if win.xshift != 0:
        if a.ndim == 3:
            slicer = (n_slice, y_long_slice, x_slice)
        else:
            slicer = (y_long_slice, x_slice)
        a[slicer] = dataset.ReadAsArray(xoff, win.m_yoff, win.margin, win.m_ysize)

    # upper or lower side
    if win.yshift != 0:
        if a.ndim == 3:
            slicer = (n_slice, y_slice, x_long_slice)
        else:
            slicer = (y_slice, x_long_slice)

        a[slicer] = dataset.ReadAsArray(win.m_xoff, yoff, win.m_xsize, win.margin)    
    
    # corners
    if win.yshift != 0 and win.xshift != 0:
        if a.ndim == 3:
            slicer = (n_slice, y_slice, x_slice)
        else:
            slicer = (y_slice, x_slice)

        a[slicer] = dataset.ReadAsArray(xoff, yoff, win.margin, win.margin)     
