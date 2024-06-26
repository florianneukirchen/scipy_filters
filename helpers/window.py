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
    Class for window (tiles) of a large raster, to be created with get_windows().
    Does not contain any data, only the parameters to read/write data with gdal
    and to slice off the margin.

    Properties:
    ===========

    gdalin: tuple with x_offset, y_offset, x_size, y_size including the margins
            of the window. To be used as parameters with gdal.Open() for input.
    gdalout: tuple with x_offset, y_offset without the margins of the window.
            To be used as parameter with gdal.Open() for output.

    Methods:
    ========

    getslice(ndim=3): Returns tuple of slice objects to be used directly with
            numpy to slice of the margin of the window. 
            ndim: int, number of dimensions of the numpy array, either 2 or 3.
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
        return self.m_xoff, self.m_yoff, self.m_xsize, self.m_ysize
    
    @property
    def gdalout(self):
        return self.xoff, self.yoff
    
    # Only for debugging:
    @property
    def gdalin_no_margin(self):
        return self.xoff, self.yoff, self.xsize, self.ysize
    
    def getslice(self, ndim=3):
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
        return f"<RasterWindow>{self.xoff} {self.yoff} margin {self.m_xoff} {self.m_yoff}"

    def get_a_off(self):
        return self.xoff, self.yoff, self.m_xoff, self.m_yoff



def get_windows(rasterXSize, rasterYSize, margin=0, windowsize=1024):
    """
    Generator yielding RasterWindow classes, dividing a large raster into smaller
    windows (tiles).
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
    """Returns the number of windows that would be created with get_windows(). Used for progress bar."""
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
    Fills the margin of windows (tiles) that are situated on the edge
    of the original dataset with the data of the far side of the dataset.
    This makes mode="wrap" (offered by some scipy filters) possible.
    The wrapping itself is done by scipy, this function only fills the
    data needed for wrapping to work.

    a: Numpy array
    dataset: gdal dataset
    win: RasterWindow
    band: int | None. Number of band (2D array), None for all bands (3D array).
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
