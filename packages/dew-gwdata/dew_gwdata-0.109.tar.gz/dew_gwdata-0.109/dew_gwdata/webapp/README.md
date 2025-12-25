# dew_gwdata web application

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
