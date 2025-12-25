############
Installation
############

Requirements
============

dew_gwdata relies on some specific Python packages to be installed in order to
work. You will need to have an Anaconda Python Distribution installed. I recommend
using "mambaforge" for this - see instruction for installing this on DEW computers
here:

file:///P:/projects_gw/State/Groundwater_Toolbox/Python/wheels/docs/dew_ws_tools/latest_source/installing_python.html

Installing dew_gwdata
========================

Once you have conda/mamba installed, you can run this in Command Prompt to install
dew_gwdata and all its dependencies:

.. code-block:: none

    conda install -c dew-waterscience dew_gwdata

(Substitute ``mamba`` for ``conda`` if you have mamba installed - if you don't know
what the difference is, just use the command above)

Updating the dew_gwdata package
==================================

You can either install the latest version from Anaconda:

.. code-block:: none

    conda update -c dew-waterscience dew_gwdata

Or you can update from PyPI:

.. code-block:: none

    pip install -U dew_gwdata

The source code is stored on the DEW Water Science Bitbucket account at 
https://bitbucket.org/dewsurfacewater/dew_gwdata. You can request access to
this by emailing Claire.Sims@sa.gov.au with your Bitbucket username.
