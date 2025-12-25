Drillhole details
====================


Replacement drillholes
-----------------------

.. code-block:: python

    >>> dhs = con.find_wells("6728-3555")
    >>> df = con.replacement_drillholes_by_dh_no(dhs)
    >>> print(df)
        dh_no unit_hyphen  new_dh_no new_unit_hyphen replaced_from
    0  203161   6728-3555     362448       6728-4467    2021-07-04

