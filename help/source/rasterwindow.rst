RasterWindow and related functions
===================================
:py:class:`helpers.RasterWindow` is used internally to process large rasters in a moving window. The windows can be generated with :py:func:`helpers.get_windows`.

:py:class:`helpers.RasterWindow` also works for processing large rasters with :py:class:`helpers.RasterWizard`.

RasterWindow
------------

.. autoclass:: helpers.RasterWindow
    :members:

Related functions
-----------------

.. autofunction:: helpers.get_windows

.. autofunction:: helpers.number_of_windows

.. autofunction:: helpers.wrap_margin