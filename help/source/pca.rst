Principal Component Analysis (PCA) — SciPy Filters for QGIS
===========================================================

Principal Component Analysis (PCA)
----------------------------------

.. versionchanged:: 1.5
    Add parameters plot and standard scaler 

.. autoclass:: scipy_filters.algs.scipy_pca_algorithm.SciPyPCAAlgorithm


Keep only n components 
----------------------

.. autoclass:: scipy_filters.algs.scipy_pca_helper_algorithms.SciPyKeepN

Transform from principal components
-----------------------------------

.. versionchanged:: 1.5
    Add parameter Std of original bands

.. autoclass:: scipy_filters.algs.scipy_pca_helper_algorithms.SciPyTransformFromPCAlgorithm

Transform to principal components
---------------------------------

.. versionchanged:: 1.5
    Add parameter Std of original bands

.. autoclass:: scipy_filters.algs.scipy_pca_helper_algorithms.SciPyTransformToPCAlgorithm


Biplot
------
.. versionadded:: 1.5
.. autoclass:: scipy_filters.algs.scipy_pca_biplot.SciPyPCABiplot


