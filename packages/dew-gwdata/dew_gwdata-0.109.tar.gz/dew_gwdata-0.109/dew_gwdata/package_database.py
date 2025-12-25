import sqlite3


def connect_to_package_database(fn=None):
    if fn is None:
        fn = r"R:\DFW_CBD\Geophyslogs\dew_gwdata.webapp\dew_gwdata.webapp.db"

    create_table = """
    CREATE TABLE IF NOT EXISTS "daily_rainfall" (
    	"id"	TEXT UNIQUE,
    	"station_id"	TEXT NOT NULL,
    	"date"	TEXT NOT NULL,
    	"rainfall"	REAL NOT NULL,
    	"interpolated_code"	INTEGER NOT NULL,
    	"quality"	INTEGER NOT NULL,
        "date_added" TEXT NOT NULL
    );
    """

    conn = sqlite3.connect(str(fn))
    cursor = conn.cursor()
    cursor.execute(create_table)
    conn.commit()

    return conn
