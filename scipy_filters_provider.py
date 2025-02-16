# -*- coding: utf-8 -*-

"""
/***************************************************************************
 SciPyFilters
                                 A QGIS plugin
 Filter collection implemented with SciPy
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-03-03
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
__date__ = '2024-03-03'
__copyright__ = '(C) 2024 by Florian Neukirchen'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from scipy_filters.helpers import tr, DEFAULTWINDOWSIZE, MAXSIZE
                                   
from scipy_filters.algs.scipy_convolve_algorithm import (SciPyConvolveAlgorithm,
                                            SciPyCorrelateAlgorithm)

from scipy_filters.algs.scipy_morphological_algorithm import (SciPyBinaryMorphologicalAlgorithm, 
                                            SciPyGreyMorphologicalAlgorithm,
                                            SciPyTophatAlgorithm)

from scipy_filters.algs.scipy_morphological_binary_fill_holes import SciPyBinaryFillHolesAlgorithm

from scipy_filters.algs.scipy_binary_hit_miss import SciPyBinaryHitMissAlgorithm

from scipy_filters.algs.scipy_gaussian_algorithm import (SciPyGaussianAlgorithm, 
                                       SciPyGaussianLaplaceAlgorithm,
                                       SciPyGaussianGradientMagnitudeAlgorithm)

from scipy_filters.algs.scipy_edge_algorithms import (SciPyLaplaceAlgorithm,
                                      SciPySobelAlgorithm,
                                      SciPyPrewittAlgorithm,)

from scipy_filters.algs.scipy_statistical_algorithms import (SciPyMedianAlgorithm,
                                      SciPyMaximumAlgorithm,
                                      SciPyMinimumAlgorithm,
                                      SciPyPercentileAlgorithm,
                                      SciPyRankAlgorithm,
                                      SciPyUniformAlgorithm,
                                      SciPyRangeAlgorithm)

from scipy_filters.algs.scipy_fourier_algorithm import (SciPyFourierGaussianAlgorithm,
                                      SciPyFFTConvolveAlgorithm,
                                      SciPyFourierEllipsoidAlgorithm,
                                      SciPyFourierUniformAlgorithm,
                                      SciPyFFTCorrelateAlgorithm)

from scipy_filters.algs.scipy_enhance_algorithms import (SciPyWienerAlgorithm,
                                       SciPyUnsharpMaskAlgorithm)


from scipy_filters.algs.scipy_local_variance_algorithm import (SciPyEstimateVarianceAlgorithm,
                                            SciPyEstimateStdAlgorithm,
                                            SciPyStdAlgorithm)

from scipy_filters.algs.scipy_pixel_statistic_algorithms import (SciPyPixelMinAlgorithm,
                                               SciPyPixelMaxAlgorithm,
                                               SciPyPixelMeanAlgorithm,
                                               SciPyPixelMedianAlgorithm,
                                               SciPyPixelRangeAlgorithm,
                                               SciPyPixelStdAlgorithm,
                                               SciPyPixelVarAlgorithm,
                                               SciPyPixelMinMaxMeanAlgorithm)

from scipy_filters.algs.scipy_pca_algorithm import SciPyPCAAlgorithm

from scipy_filters.algs.scipy_pca_helper_algorithms import (SciPyTransformToPCAlgorithm,
                                               SciPyTransformFromPCAlgorithm,
                                               SciPyKeepN)

from scipy_filters.algs.gradient_algorithm import (SciPyGradientAlgorithm,
                                      SciPyPixelGradientAlgorithm,
                                      SciPyPixelDiffAlgorithm)

from scipy_filters.algs.scipy_nodata_algorithm import (SciPyFilterNoDataMask,
                                          SciPyFilterApplyNoDataMask,
                                          SciPyFilterFillNoData)

from processing.core.ProcessingConfig import Setting, ProcessingConfig

class SciPyFiltersProvider(QgsProcessingProvider):

    def __init__(self):
        """
        Default constructor.
        """
        QgsProcessingProvider.__init__(self)

    def load(self):

        ProcessingConfig.settingIcons[self.name()] = self.icon()

        ProcessingConfig.addSetting(
            Setting(self.name(), 
                    'WINDOWSIZE', 
                    tr('Window size for processing of large rasters (edge length in pixels)'),
                    DEFAULTWINDOWSIZE,))

        ProcessingConfig.addSetting(
            Setting(self.name(), 
                    'MAXSIZE', 
                    tr('Maximum size (megapixels) for algorithms not working in a moving window (avoids crashes).'),
                    MAXSIZE,))
        
        ProcessingConfig.readSettings()
        self.refreshAlgorithms()
        return True
    

    def unload(self):
        """
        Unloads the provider. Any tear-down steps required by the provider
        should be implemented here.
        """
        if 'WINDOWSIZE' in ProcessingConfig.settings:
            ProcessingConfig.removeSetting('WINDOWSIZE')
        if 'MAXSIZE' in ProcessingConfig.settings:
            ProcessingConfig.removeSetting('MAXSIZE')

    def loadAlgorithms(self):
        """
        Loads all algorithms belonging to this provider.
        """
        self.addAlgorithm(SciPyGaussianAlgorithm())

        self.addAlgorithm(SciPyConvolveAlgorithm())
        self.addAlgorithm(SciPyCorrelateAlgorithm())

        self.addAlgorithm(SciPyBinaryMorphologicalAlgorithm())
        self.addAlgorithm(SciPyGreyMorphologicalAlgorithm())  
        self.addAlgorithm(SciPyTophatAlgorithm())      
        self.addAlgorithm(SciPyBinaryFillHolesAlgorithm())   
        self.addAlgorithm(SciPyBinaryHitMissAlgorithm()) 

        self.addAlgorithm(SciPyGaussianGradientMagnitudeAlgorithm()) 
        self.addAlgorithm(SciPyGaussianLaplaceAlgorithm()) 
        self.addAlgorithm(SciPyLaplaceAlgorithm()) 
        self.addAlgorithm(SciPySobelAlgorithm()) 
        self.addAlgorithm(SciPyPrewittAlgorithm()) 

        self.addAlgorithm(SciPyMedianAlgorithm()) 
        self.addAlgorithm(SciPyMaximumAlgorithm())
        self.addAlgorithm(SciPyMinimumAlgorithm())
        self.addAlgorithm(SciPyPercentileAlgorithm())
        self.addAlgorithm(SciPyRankAlgorithm())
        self.addAlgorithm(SciPyUniformAlgorithm())
        self.addAlgorithm(SciPyRangeAlgorithm())

        self.addAlgorithm(SciPyFourierGaussianAlgorithm())
        self.addAlgorithm(SciPyFFTConvolveAlgorithm())
        self.addAlgorithm(SciPyFourierEllipsoidAlgorithm())
        self.addAlgorithm(SciPyFourierUniformAlgorithm())
        self.addAlgorithm(SciPyFFTCorrelateAlgorithm())

        self.addAlgorithm(SciPyWienerAlgorithm())
        self.addAlgorithm(SciPyUnsharpMaskAlgorithm())

        self.addAlgorithm(SciPyEstimateVarianceAlgorithm())
        self.addAlgorithm(SciPyEstimateStdAlgorithm())
        # self.addAlgorithm(SciPyStdAlgorithm())  # VERY slow!

        self.addAlgorithm(SciPyPixelMinAlgorithm())
        self.addAlgorithm(SciPyPixelMaxAlgorithm())
        self.addAlgorithm(SciPyPixelMedianAlgorithm())
        self.addAlgorithm(SciPyPixelMeanAlgorithm())
        self.addAlgorithm(SciPyPixelRangeAlgorithm())
        self.addAlgorithm(SciPyPixelMinMaxMeanAlgorithm())
        self.addAlgorithm(SciPyPixelStdAlgorithm())
        self.addAlgorithm(SciPyPixelVarAlgorithm())

        self.addAlgorithm(SciPyPCAAlgorithm())

        self.addAlgorithm(SciPyTransformToPCAlgorithm())
        self.addAlgorithm(SciPyTransformFromPCAlgorithm())
        self.addAlgorithm(SciPyKeepN())

        self.addAlgorithm(SciPyGradientAlgorithm())        
        self.addAlgorithm(SciPyPixelGradientAlgorithm())
        self.addAlgorithm(SciPyPixelDiffAlgorithm())

        self.addAlgorithm(SciPyFilterNoDataMask())
        self.addAlgorithm(SciPyFilterApplyNoDataMask())  
        self.addAlgorithm(SciPyFilterFillNoData())  

        # PCA Biplot requires plotly
        try:
            from scipy_filters.algs.scipy_pca_biplot import SciPyPCABiplot
            self.addAlgorithm(SciPyPCABiplot())
        except ImportError:
            pass

             

    def id(self):
        """
        Returns the unique provider id, used for identifying the provider. This
        string should be a unique, short, character only string, eg "qgis" or
        "gdal". This string should not be localised.
        """
        return 'scipy_filters'

    def name(self):
        """
        Returns the provider name, which is used to describe the provider
        within the GUI.

        This string should be short (e.g. "Lastools") and localised.
        """
        return tr('SciPy Filters')

    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        # return QgsProcessingProvider.icon(self)
        return QIcon(os.path.join(os.path.dirname(__file__) + '/_static/icon/logo.png'))

    def longName(self):
        """
        Returns the a longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Lastools LIDAR tools
        (version 2.2.1)". This string should be localised. The default
        implementation returns the same string as name().
        """
        return self.name()
