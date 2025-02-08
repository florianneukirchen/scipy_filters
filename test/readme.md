# Tests Fail

The tests worked fine in October 2024, just before the release of QGIS 3.40.
Now discovery of tests segfaults, running all tests segfaults, but running
each test individually works fine. 

I have spent half a day with the help of chatgpt and copilot, but I could 
not find the reason. I suspect it is somehow related to GDAL.

I leave the tests as experimental.