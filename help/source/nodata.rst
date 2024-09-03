No Data filters — SciPy Filters for QGIS
========================================

In QGIS, filters normally ignore No Data cells automatically. However, this is not always easy, especially if a filter examines neighboring cells and these contain No Data. What happens depends on the implementation, but is problematic in both cases.

In raster layers, “No Data” is coded with a specific number, e.g. -9999. If, for example, the mean value within a 3✕3 neighborhood is calculated, the result in the vicinity of each No Data cell is of course nonsense. If you replace the -9999 (in Numpy) with NaN (which is only possible with float), the respective cell will become No Data as well, because a calculation is not possible. The No Data cells infect their neighbors, so to speak.

One possibility is to fill the no-data cells with any reasonably meaningful value. QGIS itself and GDAL offer various ways of doing this, but these have the disadvantage that only one single band is processed at a time. You would therefore have to process each band individually and then merge the results back into one layer.

The QGIS plugin Scipy Filters allows to fill no-data cells in all bands, with:

* Null
* A user-defined constant
* The mean value of the band (estimated by GDAL or calculated exactly)
* The minimum value of the data type
* The maximum value of the data type
* The central value of the data type

To track which cells were originally “No Data”, the plugin can also create a No Data mask (binary raster with 0 and 1) and apply this mask to a raster layer, i.e. set the corresponding cells back to No Data.

Apply no data mask 
------------------

.. autoclass:: scipy_filters.algs.scipy_nodata_algorithm.SciPyFilterApplyNoDataMask

Fill no data
------------

.. autoclass:: scipy_filters.algs.scipy_nodata_algorithm.SciPyFilterFillNoData

No data mask
------------

.. autoclass:: scipy_filters.algs.scipy_nodata_algorithm.SciPyFilterNoDataMask


