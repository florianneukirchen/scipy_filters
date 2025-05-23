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

from osgeo import gdal
import numpy as np
import json
from qgis.PyQt.QtCore import QCoreApplication
from qgis._core import QgsProcessingContext, QgsProcessingFeedback
from qgis.core import (QgsProcessingAlgorithm,
                       QgsProcessingParameterString,
                       QgsProcessingParameterDefinition,
                       QgsProcessingParameterNumber,
                       QgsProcessingException,
                       QgsProcessingLayerPostProcessorInterface,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterRasterDestination)

from processing.core.ProcessingConfig import ProcessingConfig


from scipy_filters.helpers import (str_to_array, 
                      convert_docstring_to_html,
                      bandmean,
                      MAXSIZE)

from scipy_filters.scipy_algorithm_baseclasses import groups
from scipy_filters.ui.i18n import tr


class SciPyTransformPcBaseclass(QgsProcessingAlgorithm):
    """
    Baseclass to transform to/from principal components using matrix of eigenvectors

    """

    EIGENVECTORS = 'EIGENVECTORS'
    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    BANDMEAN = 'BANDMEAN'
    BANDSTD = 'BANDSTD'
    DTYPE = 'DTYPE'


    NODATA = -9999

    _groupid = "pca" 
    _name = ''
    _displayname = ''
    _outputname = ""

    # _outbands = 1

    _inverse = False
    _keepbands = 0
    falsemean = False

    _bandmean = None
    _bandstd = None

    V = None
    abstract = ""

    def initAlgorithm(self, config):
        try:
            self.maxsize = int(ProcessingConfig.getSetting('MAXSIZE'))
        except TypeError:
            self.maxsize = MAXSIZE

        # Add parameters

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                tr('Input layer'),
            )
        )

        eig_param = QgsProcessingParameterString(
            self.EIGENVECTORS,
            tr('Eigenvectors'),
            defaultValue="",
            multiLine=True,
            optional=True,
            )
        
        if self._inverse:
            eig_param.setFlags(eig_param.flags() | QgsProcessingParameterDefinition.Flag.FlagAdvanced)
        
        self.addParameter(eig_param)

        if self._inverse:
            desc = tr('Mean of original bands')
        else:
            desc = tr('False mean for each band')

        mean_param = QgsProcessingParameterString(
            self.BANDMEAN,
            desc,
            defaultValue="",
            multiLine=False,
            optional=True,
            )
        
        mean_param.setFlags(mean_param.flags() | QgsProcessingParameterDefinition.Flag.FlagAdvanced)
      
        self.addParameter(mean_param)

        std_param = QgsProcessingParameterString(
            self.BANDSTD,
            tr('Std of original bands if standard scaler was used, otherwise leave empty'),
            defaultValue="",
            multiLine=False,
            optional=True,
            )

        std_param.setFlags(std_param.flags() | QgsProcessingParameterDefinition.Flag.FlagAdvanced)

        self.addParameter(std_param)

        dtype_param = QgsProcessingParameterEnum(
            self.DTYPE,
            tr('Output data type'),
            ['Float32 (32 bit float)', 'Float64 (64 bit float)'],
            defaultValue=0,
            optional=True)
        
        # Set as advanced parameter
        dtype_param.setFlags(dtype_param.flags() | QgsProcessingParameterDefinition.Flag.FlagAdvanced)
        self.addParameter(dtype_param)


        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
            tr(self._outputname)))
        
    
    def get_parameters(self, parameters, context):
        
        self.inputlayer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        self.output_raster = self.parameterAsOutputLayer(parameters, self.OUTPUT,context)

        # eigenvectors from text field
        V = self.parameterAsString(parameters, self.EIGENVECTORS, context)
        self.V = str_to_array(V, dims=None, to_int=False)

        # Parameters from metadata abstract
        if self._inverse:
            self.abstract = self.inputlayer.metadata().abstract()
            # The other case is handled in the inheriting class

        eigenvectors, means, bandstd = self.json_to_parameters(self.abstract)


        if self.V is None:
            self.V = eigenvectors

        # Get the mean, start with metadata of layer and eventually overwrite it
        if self._inverse or self.falsemean:    
            if means is None:
                means = 0
            if isinstance(means, np.ndarray) and means.ndim == 1:
                means = means[np.newaxis, :]

            self._bandmean = means

            # Mean from text field
            bandmean = self.parameterAsString(parameters, self.BANDMEAN, context)

            bandmean = bandmean.strip()

            if bandmean != "":
                if not (bandmean[0] == "[" and bandmean[-1] == "]"):
                    bandmean = "[" + bandmean + "]"
                try:
                    decoded = json.loads(bandmean)
                    a = np.array(decoded)
                except (json.decoder.JSONDecodeError, ValueError, TypeError):
                    a = None

                if not a is None:
                    self._bandmean = a[np.newaxis, :]
        
        # Get the standard deviations,  start with metadata of layer and eventually overwrite it
        if isinstance(bandstd, np.ndarray) and bandstd.ndim == 1:
            self._bandstd = bandstd[np.newaxis, :]

        bandstd = self.parameterAsString(parameters, self.BANDSTD, context)
        bandstd = bandstd.strip()

        if bandstd != "":
            if not (bandstd[0] == "[" and bandstd[-1] == "]"):
                bandstd = "[" + bandstd + "]"
            try:
                decoded = json.loads(bandstd)
                a = np.array(decoded)
            except (json.decoder.JSONDecodeError, ValueError, TypeError):
                a = None

            if not a is None:
                self._bandstd = a[np.newaxis, :]


        self.outdtype = self.parameterAsInt(parameters, self.DTYPE, context)
        self.outdtype = self.outdtype + 6 # float32 and float64 in gdal

    def checkParameterValues(self, parameters, context):
        layerstds = None

        inputlayer = self.parameterAsRasterLayer(parameters, self.INPUT, context)

        if not inputlayer.providerType() == "gdal":
            return False, tr("Raster provider {} is not supported, must be raster layer with a local file".format(inputlayer.providerType()))

        bands = inputlayer.bandCount()

        # Check maxsize
        size = inputlayer.width() * inputlayer.height() / 1000000 # megapixels
        if size > self.maxsize:
            return False, tr("Raster size is larger than maxsize (see settings).")


        V = self.parameterAsString(parameters, self.EIGENVECTORS, context)
        V = V.strip()

        # Check eigenvectors (text field)
        try:
            V = str_to_array(V, dims=None, to_int=False)
        except QgsProcessingException:
            return False, tr("Can not parse eigenvectors")

        # Get parameters from metadata and check eigenvectors
        if self._inverse:
            abstract = inputlayer.metadata().abstract()
            checkmean = True
        else:
            paramlayer = self.parameterAsRasterLayer(parameters, self.PARAMETERLAYER, context)
            if paramlayer:
                abstract = paramlayer.metadata().abstract()
            else:
                abstract = ""
            checkmean = self.parameterAsBool(parameters, self.FALSEMEAN, context)

        eigenvectors, layermeans = None, ""

        abstract = abstract.strip()
        if not abstract == "":
            try:
                decoded = json.loads(abstract)
            except (json.decoder.JSONDecodeError, ValueError, TypeError):
                return False, tr("Could not decode metadata abstract")
            eigenvectors = decoded.get("eigenvectors", None)
            layermeans = decoded.get("band mean", "")
            layerstds = decoded.get("band std", None)

            if not eigenvectors is None:
                try:
                    eigenvectors = np.array(eigenvectors)
                except (ValueError, TypeError):
                    return False, tr("Could not decode metadata abstract")
            
        # Check if eigenvectors are provided one or the other way
        if V is None:
            V = eigenvectors
        if V is None:
            return False, tr("The layer does not contain valid eigenvectors and no eigenvectors where provided")

        # Check dimensions and shape of eigenvectors
        if V.ndim != 2 or V.shape[0] != V.shape[1]:
            return False, tr("Matrix of eigenvectors must be square (2D)")

        if (self._inverse and V.shape[0] < bands) or ((not self._inverse) and V.shape[0] != bands):
            return False, tr("Shape of matrix of eigenvectors does not match number of bands")


        # Check provided means
        if checkmean:
            if isinstance(layermeans, list) and len(layermeans) > 1:
                layermeans = np.array(layermeans)

            # Start with mean from text field
            bandmean = self.parameterAsString(parameters, self.BANDMEAN, context)

            bandmean = bandmean.strip()
            if bandmean != "":
                if not (bandmean[0] == "[" and bandmean[-1] == "]"):
                    bandmean = "[" + bandmean + "]"
            
            if not bandmean == "":
                try:
                    decoded = json.loads(bandmean)
                    bandmean = np.array(decoded)
                except (json.decoder.JSONDecodeError, ValueError, TypeError):
                    return False, tr("Could not parse list of means")
                # If mean is given in text field, do not use the one from metadata
                layermeans = bandmean

            # Check dimensions (both cases) 
            if layermeans.ndim != 1:
                return False, tr("False shape of means list")
            if layermeans.shape[0] != V.shape[0]:
                return False, tr("False shape of means list")
            
        # Check provided standard deviations
        if isinstance(layerstds, list) and len(layerstds) > 1:
            layerstds = np.array(layerstds)
        
        bandstd = self.parameterAsString(parameters, self.BANDSTD, context)
        bandstd = bandstd.strip()
        if bandstd != "":
            if not (bandstd[0] == "[" and bandstd[-1] == "]"):
                bandstd = "[" + bandstd + "]"

        if not bandstd == "":
            try:
                decoded = json.loads(bandstd)
                bandstd = np.array(decoded)
            except (json.decoder.JSONDecodeError, ValueError, TypeError):
                return False, tr("Could not parse list of standard deviations")
            layerstds = bandstd

        if not layerstds is None:
            if layerstds.ndim != 1:
                return False, tr("False shape of standard deviations list")
            if layerstds.shape[0] != V.shape[0]:
                return False, tr("False shape of standard deviations list")

        return super().checkParameterValues(parameters, context)


    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        self.get_parameters(parameters, context)


        self.ds = gdal.Open(self.inputlayer.source())

        if not self.ds:
            raise Exception("Failed to open Raster Layer")
        
        self.bandcount = self.ds.RasterCount
        bands = self._keepbands        
        if bands == 0 or bands > self.bandcount:
            bands = self.bandcount

        # Get no data value from band 1. 
        # Geotiff only has one no data value, other formats could have different ones 
        # per band, so this is not optimal
        nodatavalue = self.ds.GetRasterBand(1).GetNoDataValue()

        if feedback.isCanceled():
            return {}
        
        feedback.setProgress(0)

        # Get band mean
        if not self._inverse:
            if not self.falsemean:
                # Calculate band mean using GDAL
                means = []
                for b in range(1, self.ds.RasterCount + 1):
                    means.append(bandmean(self.ds, b, approx=False))
                    self._bandmean = np.array(means)
                    self._bandmean = self._bandmean[np.newaxis, :]
                feedback.pushInfo(tr("\nBand Mean:"))
            else:
                feedback.pushInfo(tr("\nFalse (given) band mean:"))
            feedback.pushInfo(str(self._bandmean[0].tolist()) + "\n")


        # Start the actual work
        if self.outdtype == 6:
            a = self.ds.ReadAsArray().astype(np.float32)
        else:
            a = self.ds.ReadAsArray().astype(np.float64)
        if a.ndim == 2: # Layer with only 1 band
            a = a[np.newaxis, :]
        
        orig_shape = a.shape

        # Flatten 
        a = a.reshape(orig_shape[0], -1)
        a = a.T

        nodata_mask = np.any(a == nodatavalue, axis=1)

        # substract mean
        if not self._inverse:
            if not self.falsemean:
                feedback.pushInfo(tr("\nBand Mean:"))
            else:
                feedback.pushInfo(tr("\nFalse (given) band mean:"))
            feedback.pushInfo(str(self._bandmean[0].tolist()) + "\n")

            a = a - self._bandmean

            # Scale data
            if not self._bandstd is None:
                a = a / self._bandstd


        # Transform to PC
        if self._inverse:
            components = self.V.T # Same as VT from the SVD in the PCA algorithm
            # If not all PC bands were kept
            if self.bandcount < components.shape[0]:
                bands = components.shape[0]
                orig_shape = (bands, orig_shape[1], orig_shape[2])
                
                components = components[0:self.bandcount,:]

        else:
            components = self.V

        # Transformation is dot product of data array (shape: n_pixels x bands) with V (forward) or VT (inverse)
        new_array = a @ components

        # Add the original band means
        if self._inverse:
            if not self._bandstd is None:
                new_array = new_array * self._bandstd

            new_array = new_array + self._bandmean

        # Set no data value
        new_array[nodata_mask] = self.NODATA

        # Flattened array back to normal shape
        new_array = new_array.T.reshape(orig_shape)

        if feedback.isCanceled():
            return {}
        
        # Prepare output and write file

        driver = gdal.GetDriverByName('GTiff')
        self.out_ds = driver.Create(self.output_raster,
                                    xsize=self.ds.RasterXSize,
                                    ysize=self.ds.RasterYSize,
                                    bands=bands,
                                    eType=self.outdtype)

        self.out_ds.SetGeoTransform(self.ds.GetGeoTransform())
        self.out_ds.SetProjection(self.ds.GetProjection())

        self.out_ds.WriteArray(new_array[0:bands,:,:])    


        # Set no data value
        if nodatavalue is not None:
            for b in range(1, bands + 1):
                self.out_ds.GetRasterBand(b).SetNoDataValue(self.NODATA)


        # Calculate and write band statistics (min, max, mean, std)
        for b in range(1, bands + 1):
            band = self.out_ds.GetRasterBand(b)
            stats = band.GetStatistics(0,1)
            band.SetStatistics(*stats)

        # Close the dataset to write file to disk
        self.out_ds = None 

        self.ds = None
        a = None
        new_array = None
       
        if self._inverse:
            return {
                self.OUTPUT: self.output_raster,
                'eigenvectors': self.V,
                }
        else:
            encoded = json.dumps({
                'eigenvectors': self.V.tolist(),
                'band mean': self._bandmean[0].tolist(),
            })

            global updatemetadata
            updatemetadata = self.UpdateMetadata(encoded)
            context.layerToLoadOnCompletionDetails(self.output_raster).setPostProcessor(updatemetadata)


            return {
                self.OUTPUT: self.output_raster,
                'band mean': self._bandmean[0],
                'eigenvectors': self.V,
                }
                

    def json_to_parameters(self, s):
        """
        Get eigenvectors, band means and eventually band stds from json string
        
        Band means have been used for centering data, stds for scaling.

        Returns: 
        
        eigenvectors: np.array | None, 
        means: np.array | None
        stds: np.array | None
        """
        if s is None:
            return None, None, None
        
        s = s.strip()
        if s == "":
            return None, None, None
        try:
            decoded = json.loads(s)
        except (json.decoder.JSONDecodeError, ValueError, TypeError):
            return None, None, None

        eigenvectors = decoded.get("eigenvectors", None)

        try:
            eigenvectors = np.array(eigenvectors)
        except (ValueError, TypeError):
            eigenvectors = None

        means = decoded.get("band mean", 0)
        try:
            means = np.array(means)
        except (ValueError, TypeError):
            means = None

        stds = decoded.get("band std", None)
        try:
            stds = np.array(stds)
        except (ValueError, TypeError):
            stds = None

        return eigenvectors, means, stds


    class UpdateMetadata(QgsProcessingLayerPostProcessorInterface):
        """
        To add metadata in the postprocessing step.
        """
        def __init__(self, abstract):
            self.abstract = abstract
            super().__init__()
            
        def postProcessLayer(self, layer, context, feedback):
            meta = layer.metadata()
            meta.setAbstract(self.abstract)
            layer.setMetadata(meta)

    def name(self):
        return self._name

    def displayName(self):
        return tr(self._displayname)

    def group(self):
        if self._groupid == "":
            return ""
        s = groups.get(self._groupid)
        if not s:
            # If group ID is not in dictionary group, return error message for debugging
            return "Displayname of group must be set in groups dictionary"
        return tr(s)

    def groupId(self):
        return self._groupid
    
    def shortHelpString(self):
        docstring = self.__doc__
        return convert_docstring_to_html(docstring)

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)


    
class SciPyTransformToPCAlgorithm(SciPyTransformPcBaseclass):
    """
    Transform to principal components

    Transform data into given principal components 
    with a matrix of eigenvectors by taking the 
    dot product with a matrix of weights (after centering or scaling the data). 


    The eigenvectors can also be read from the metadata of an 
    existing PCA layer. 

    **Eigenvectors** Matrix of eigenvectors (as string). 
    Optional if the next parameter is set. 
    

    **Read eigenvectors from PCA layer metadata** 
    Reads the weights for the transformation from the metadata 
    of a layer that was generated using the PCA algorithm of this plugin. 
    Ignored if the parameter *eigenvectors* is used. 

    **Number of components** is only used if the value is greater than 0 and 
    smaller than the count of original bands.

    **False mean for each band** As first step of PCA, the data of each 
    band is centered by subtracting the means. If false means are provided, 
    these are substracted instead of the real means of the input layer. 
    This allows to transform another raster image into the same space 
    as the principal components of another layer. The result is usefull 
    for comparation of several rasters, but should not be considered to be 
    proper principal components. Only used if "Used false mean" is checked.

    **Use false mean** See also *false mean of each band*. The 
    false mean to be used can also be read from the metadata of a PCA layer. 

    **Std of original bands** Empty string (no scaling) or list of standard deviations
    for each band of the original data that was used for PCA. If provided, the data is 
    scaled by dividing by the provided standard deviations. 
    
    **Output data type** Float32 or Float64.
    """

    _name = 'transform_to_PC'
    _displayname = tr('Transform to principal components')
    _outputname = _displayname


    PARAMETERLAYER = "PARAMETERLAYER"
    NCOMPONENTS = 'NCOMPONENTS'
    FALSEMEAN = 'FALSEMEAN'

    def createInstance(self):
        return SciPyTransformToPCAlgorithm()  
    
    def initAlgorithm(self, config):
        super().initAlgorithm(config)

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.PARAMETERLAYER,
                tr('Read eigenvectors from PCA layer metadata'),
                optional=True,
            )
        )

        self.addParameter(QgsProcessingParameterNumber(
            self.NCOMPONENTS,
            tr('Number of components to keep. Set to 0 for all components.'),
            QgsProcessingParameterNumber.Type.Integer,
            defaultValue=0, 
            optional=True, 
            minValue=0, 
            # maxValue=100
            ))
        
        means_b = QgsProcessingParameterBoolean(
            self.FALSEMEAN,
            tr('Use false mean (provided as parameter) to center data'),
            optional=True,
            defaultValue=False,
        )

                
        means_b.setFlags(means_b.flags() | QgsProcessingParameterDefinition.Flag.FlagAdvanced)
      
        self.addParameter(means_b)

    def get_parameters(self, parameters, context):
        paramlayer = self.parameterAsRasterLayer(parameters, self.PARAMETERLAYER, context)
        if paramlayer:
            self.abstract = paramlayer.metadata().abstract()
        
        self._keepbands = self.parameterAsInt(parameters, self.NCOMPONENTS, context)
        self.falsemean = self.parameterAsBool(parameters, self.FALSEMEAN, context)

        super().get_parameters(parameters, context)



class SciPyTransformFromPCAlgorithm(SciPyTransformPcBaseclass):
    """
    Transform from principal components
    
    Transform data from principal components (i.e. the PCA scores) 
    back into the original feature space 
    using a matrix of eigenvectors by taking the 
    dot product of the scores the with the transpose of the matrix of eigenvectors 
    and adding the original means to the result.

    The eigenvectors can also be read from the metadata 
    of the input layer, as long as they exist and are complete. 

    **Eigenvectors** Matrix of eigenvectors (as string). 
    Optional if the next parameter is set. 
    The matrix can be taken from the output of the PCA algorith of this plugin. 

    **Mean of original bands** As first step of PCA, the data of each 
    band is centered by subtracting the means. These must be added 
    after rotating back into the original feature space. 
    Optional if the meta data of the input layer is complete. 
    (Use false means if they were used for the forward transformation.)

    **Std of original bands** Empty string (no scaling was used) or list of standard deviations
    for each band of the original data that was used for PCA. 
            
    **Output data type** Float32 or Float64.
    """

    _name = 'transform_from_PC'
    _displayname = tr('Transform from principal components')
    _outputname = _displayname

    _inverse = True


    def createInstance(self):
        return SciPyTransformFromPCAlgorithm()  
    

class SciPyKeepN(QgsProcessingAlgorithm):
    """
    Keep only n components
    
    Utility to remove components of lesser importance 
    after a principal components analysis (PCA)
    
    **Number of components** to keep. Negative numbers:  
    numbers of components to remove.
    """

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    NCOMPONENTS = 'NCOMPONENTS'

    _name = 'keep_only'
    _displayname = tr('Keep only n components')

    # Init Algorithm
    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # Add parameters
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                tr('Input layer'),
            )
        )

        self.addParameter(QgsProcessingParameterNumber(
            self.NCOMPONENTS,
            tr('Number of components to keep (negative: number of components to remove)'),
            QgsProcessingParameterNumber.Type.Integer,
            defaultValue=-1, 
            optional=False, 
            # minValue=1, 
            # maxValue=100
            ))      
    
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
            tr(self._displayname)))
        
    def processAlgorithm(self, parameters, context, feedback):

        # Get Parameters
        self.inputlayer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        self.output_raster = self.parameterAsOutputLayer(parameters, self.OUTPUT,context)

        self.ncomponents = self.parameterAsInt(parameters, self.NCOMPONENTS,context)

        # Open Raster with GDAL
        self.ds = gdal.Open(self.inputlayer.source())

        if not self.ds:
            raise Exception("Failed to open Raster Layer")
        
        self.bandcount = self.ds.RasterCount

        if self.bandcount < abs(self.ncomponents):
            feedback.pushInfo(tr("Number of components can't be larger than band count, keeping all bands."))
            self.ncomponents = self.bandcount

        if self.ncomponents <= 0:
            self.ncomponents = self.bandcount + self.ncomponents

        self.indatatype = self.ds.GetRasterBand(1).DataType
        nodatavalue = self.ds.GetRasterBand(1).GetNoDataValue()
       
        a = self.ds.ReadAsArray()

        # Prepare output and write array
        driver = gdal.GetDriverByName('GTiff')
        self.out_ds = driver.Create(self.output_raster,
                                    xsize=self.ds.RasterXSize,
                                    ysize=self.ds.RasterYSize,
                                    bands=self.ncomponents,
                                    eType=self.ds.GetRasterBand(1).DataType)

        self.out_ds.SetGeoTransform(self.ds.GetGeoTransform())
        self.out_ds.SetProjection(self.ds.GetProjection())

        self.out_ds.WriteArray(a[0:self.ncomponents,:,:])

        # Set no data value
        if nodatavalue is not None:
            for b in range(1, self.ncomponents + 1):
                self.out_ds.GetRasterBand(b).SetNoDataValue(nodatavalue)

        # Calculate and write band statistics (min, max, mean, std)
        for b in range(1, self.ncomponents + 1):
            band = self.out_ds.GetRasterBand(b)
            stats = band.GetStatistics(0,1)
            band.SetStatistics(*stats)

        # Copy band description
        for i in range(self.ncomponents):
            band_out = self.out_ds.GetRasterBand(i + 1)
            band_in = self.ds.GetRasterBand(i + 1)
            band_out.SetDescription(band_in.GetDescription())

        # Close the dataset to write file to disk
        self.out_ds = None 


        # Copy Metadata and set name
        global postprocess
        meta = self.inputlayer.metadata()
        name = tr("{} components of {}").format(self.ncomponents, self.inputlayer.name())
        postprocess = self.PostProcess(meta, name)
        context.layerToLoadOnCompletionDetails(self.output_raster).setPostProcessor(postprocess)


        return {self.OUTPUT: self.output_raster}
    
    def checkParameterValues(self, parameters, context):

        inputlayer = self.parameterAsRasterLayer(parameters, self.INPUT, context)

        if not inputlayer.providerType() == "gdal":
            return False, tr("Raster provider {} is not supported, must be raster layer with a local file".format(inputlayer.providerType()))
        
        return super().checkParameterValues(parameters, context)
    

    class PostProcess(QgsProcessingLayerPostProcessorInterface):
        """
        To add metadata in the postprocessing step.
        """
        def __init__(self, meta, name):
            self.meta = meta
            self.name = name
            super().__init__()
            
        def postProcessLayer(self, layer, context, feedback):
            layer.setMetadata(self.meta)
            layer.setName(self.name)

    def shortHelpString(self):
        """
        Returns the help string that is shown on the right side of the 
        user interface.
        """
        docstring = self.__doc__
        return convert_docstring_to_html(docstring)
    
    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return self._name

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return tr(self._displayname)

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        s = groups.get("pca")
        return tr(s)

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "pca"

    def createInstance(self):
        return SciPyKeepN()  