# How to install ``dew_gwdata``

First you need to open Command Prompt:

![](install_fig0.png)

Now confirm that you can run Python from it:

![](install_fig1.png)

If you get an error that "python cannot be found", come see [me](mailto:kent.inverarity@sa.gov.au) for help

You will need to install some dependencies using ``conda``:

```
conda install geopandas sqlparse click cx_Oracle pillow numpy sqlalchemy
```

Now install ``dew_gwdata`` using the command:

```
pip install -i http://envtelem04:8090 dew_gwdata
```

![](install_fig3.png)

And you should be all good! If you want to upgrade later on:

```
pip install -U -i http://envtelem04:8090 dew_gwdata
```