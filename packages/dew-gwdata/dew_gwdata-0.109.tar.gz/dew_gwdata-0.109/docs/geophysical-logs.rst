   
Geophysical logging data
==========================

Geophysical logging data that was collected over the years by geophysical logging trucks
operated by the department and its predecessors is indexed and stored in SA Geodata.
It is organized into jobs, and each job is assigned a number, which then has an 
accompanying record in SA Geodata. Some metadata around these numbers can be obtained
through the predefined query :meth:`dew_gwdata.SAGeodataConnection.geophys_log_metadata`.

The data itself is generally stored in files which are organized into folders on a
network drive. There is one folder for each job number.

Converting Logger20 data files to LAS
----------------------------------------

From the 1990s until 2016, the department used MS-DOS software called Logger20 to 
acquire logging data. This produces a number of binary files with extensions that are
named for each type of probe being run e.g. ``.G`` for gamma, ``.N`` for neutron, ``.CAL``
for caliper. There is also usually a file with header information with the extension
``.HEA``. The Logger20 software can be used to read these files and create a LAS file
(Log ASCII Standard) which is a text file containing data in a spreadsheet-like layout.

However, for some jobs, the LAS file was never created, because at the time the more
useful format was a physical print out.

dew_gwdata includes a utility program to run Logger20 in DOS emulation mode, using the 
free software DOSBox, so that this LAS file can be created and saved. This utility
program is called ``logger20`` as well. To use it, you will need to make sure that DOSBox
is already installed on your computer. I recommend using 
`DOSBox Portable <https://portableapps.com/apps/games/dosbox_portable>`__. You can install
this under ``c:\devapps\app`` without any need for BTI involvement. Alternatively, DOSBox
is approved by BTI, so you can call the Helpdesk and ask them to install it. Once installed,
make sure it is on your PATH environment variable.

You can then run the Logger20 emulation program. Let's say you want to process the data 
in job 4655. You can do this directly:

.. code-block::

    > logger20 --job 4655

This will copy the data files from job 4655 into a temporary folder, launch DOSBox in 
there, and then when you are finished, it will copy any new LAS files back into the
original job 4655 folder. It will not edit or delete any original Logger20 files from
the job folder.

It assumes that you installed DOSBoxPortable.exe. 
If you instead installed the normal DOSBox, you may need to tell it what the appropriate 
name of the DOSBox executable is, e.g.

.. code-block::

    > logger20 --dosbox DOSBox.exe --job 4655

You can also pass it the name of a folder directly, in case you are not working from 
a job number, or you are not on the network:

.. code-block::

    > logger20 --path c:\my_folder\data

WORK IN PROGRESS: Add instructions for how to use Logger 20 :-(

