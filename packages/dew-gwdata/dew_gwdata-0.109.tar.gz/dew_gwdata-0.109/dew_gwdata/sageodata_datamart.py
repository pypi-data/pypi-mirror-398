import pyodbc


def get_sageodata_datamart_connection():
    """Return a pyodbc connection to the production SA Geodata
    datamart SQL Server database.

    (sql2012-prod.env.sa.gov.au)

    """
    conn = pyodbc.connect(
        "Driver={SQL Server};"
        "Server=sql2012-prod.env.sa.gov.au;"
        "Database=SAGeoData_DataMart;"
        "Trusted_Connection=yes;"
    )
    return conn
