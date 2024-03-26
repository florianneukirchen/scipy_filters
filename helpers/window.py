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


class RasterWindow():
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
    if windowsize == None:
        # get 1 window with full raster 
        yield RasterWindow(rasterXSize, rasterYSize, 0, 0, rasterXSize, rasterYSize, margin=0)

    if (rasterXSize * rasterYSize) < (windowsize**2 * 4):
        # Only create windows if the area is >= 4 * windowsize
        yield RasterWindow(rasterXSize, rasterYSize, 0, 0, rasterXSize, rasterYSize, margin=0)
    
    for x in range(0, rasterXSize, windowsize):

        if x + windowsize > rasterXSize:
            xsize = rasterXSize - x 
        else:
            xsize = windowsize

        for y in range(0, rasterYSize, windowsize):

            if y + windowsize > rasterYSize:
                ysize = rasterYSize - y 
            else:
                ysize = windowsize
                
            yield RasterWindow(rasterXSize, rasterYSize, x, y, xsize, ysize, margin)


def number_of_windows(rasterXSize, rasterYSize, windowsize):
    if windowsize == None:
        return 1
    # Only create windows if the area is >= 4 * windowsize
    if rasterXSize * rasterYSize < (windowsize**2 * 4):
        return 1
    x = np.ceil(rasterXSize / windowsize)
    y = np.ceil(rasterYSize / windowsize)
    return int(x * y)
    