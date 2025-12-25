# dew_gwdata

Python module for accessing groundwater data internally at DEW

## Install

The source code is on [Bitbucket](https://bitbucket.org/dewsurfacewater/dew_gwdata), while Python packages (source and binary) are published on
the [Python Package Index](https://pypi.org/project/dew-gwdata/) and 
on a dedicated channel on [Anaconda Cloud](https://anaconda.org/dew-waterscience/repo).

### From PyPI (most recent release)

Run this in Command Prompt to install from PyPI:

```
pip install dew_gwdata
```

To upgrade to the latest version:

```
pip install -U dew_gwdata
```

### From Anaconda 

You can also install using conda/mamba if you prefer:

```
mamba install -c dew-waterscience dew_gwdata
```

To upgrade:

```
mamba upgrade -c dew-waterscience dew_gwdata
```

The version may not be as up-to-date as the PyPI version.

### From Bitbucket

This is how you can install the latest version of the source code directly from Bitbucket (the version control repository):

```
python -m pip install git+https://kinveraritysagov@bitbucket.org/dewsurfacewater/dew_gwdata.git
```

You will need to replace ``kinveraritysagov`` with your Bitbucket username, and you will also need access to the source repository on the Bitbucket dewsurfacewater workspace.

## Usage

Check out complete documentation at:

[http://bunyip:8191/python-docs/dew_gwdata/latest_source/index.html](http://bunyip:8191/python-docs/dew_gwdata/latest_source/index.html)

## Webapp usage

"New" Waterkennect is implemented by the ``dew_gwdata.webapp`` module. To execute the webapp navigate to the folder
containing the source code, i.e. the ``dew_gwdata/webapp`` folder within this repository, and run:

```
uvicorn dew_gwdata.webapp.main:app --port 8191 --host 0.0.0.0 --reload --log-config .\log-config.yaml
```

There is an example logging config file in this folder.

```
(py310) C:\devapps\syski\code\dew_gwdata\dew_gwdata\webapp>uvicorn dew_gwdata.webapp.main:app --port 8191 --host 0.0.0.0 --reload --log-config .\log-config.yaml
INFO:     [29-11-2023 13:39:10] uvicorn.error.serve - Started server process [63528]
INFO:     [29-11-2023 13:39:10] uvicorn.error.startup - Waiting for application startup.
INFO:     [29-11-2023 13:39:10] uvicorn.error.startup - Application startup complete.
DEBUG:    [29-11-2023 13:39:41] dew_gwdata.webapp.models.queries.find_wells - id_types requested: ['unit_no', 'obs_no', 'dh_no']
INFO:     [29-11-2023 13:39:42] 10.55.65.0:58877 - "GET /app/wells_summary?idq=86711&idq_unit_no=1&idq_obs_no=1&idq_dh_no=1&env=prod HTTP/1.1" 200 OK
```


## License

All rights reserved DEW 2023
