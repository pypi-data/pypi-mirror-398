Charts
=======

Colours and markers
-------------------

There are a variety of "qualifier" fields in SA Geodata and Aquarius. dew_gwdata has some predefined colours and markers for the different values these fields can take.

Water sample data (e.g. salinity)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

extract_method stores how a water sample was obtained. It's encoded in dew_gwdata by marker shape:

.. code-block:: python

    >>> import dew_gwdata as gd
    >>> gd.EXTRACT_METHOD_LUT
    {'AIRL': 'Air Lift',
    'BAIL': 'Bailer',
    'BUCK': 'Bucket',
    'EST': 'Estimated',
    'FLOW': 'Flow',
    'HAND': 'Hand',
    'PUMP': 'Pump',
    'UKN': 'Unknown',
    'WMLL': 'Windmill',
    '?': '?'}
    >>> gd.extract_method_markers
    {'AIRL': '$a$',
    'BAIL': 'v',
    'BUCK': '>',
    'EST': '$?$',
    'FLOW': 'P',
    'HAND': '<',
    'PUMP': 'o',
    'UKN': '.',
    'WMLL': 'o',
    '?': '.'}
 
.. figure:: figures/extract_method.png

measured_during stores what kind of activity was being undertaken when the
water sample was taken. It's encoded in dew_gwdata using colour:

.. code-block:: python

    >>> gd.measured_during_lut
    {'A': 'Aquifer Test',
    'D': 'Drilling',
    'F': 'Field Survey',
    'S': 'Final Sample on drilling completion',
    'G': 'Geophysical Logging',
    'L': 'Landowner Sample',
    'M': 'Monitoring',
    'R': 'Rehabilitation',
    'U': 'Unknown',
    'W': 'Well Yield',
    '?': '?'}
    >>> gd.measured_during_colours
    {'M': 'tab:cyan',
    'F': 'tab:blue',
    'A': 'tab:green',
    'W': 'tab:olive',
    'L': 'tab:pink',
    'G': 'tab:purple',
    'D': 'tab:red',
    'S': 'tab:orange',
    'R': 'tab:brown',
    'U': 'tab:gray',
    '?': 'black'}

.. figure:: figures/measured_during.png

 