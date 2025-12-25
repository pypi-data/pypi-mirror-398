from datetime import datetime

import pandas
import ausweather


def write_daily_rainfall_to_db(station_id, df, conn):
    """Write daily rainfall data to the database.

    Args:
        station_id (str)
        df (pd.DataFrame): daily data with columns "date", "rainfall", "interpolated_code", and "quality"
        conn (sqlite3.Connection): the table "daily_rainfall" will be used.

    """
    if isinstance(station_id, float):
        station_id = int(station_id)
    station_id = str(station_id)

    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")

    for idx, row in df.iterrows():
        db_id = f"{station_id}.{row.date.strftime('%Y%m%d')}"
        values = (
            db_id,
            station_id,
            row["date"].strftime("%Y-%m-%d"),
            row.rainfall,
            row.interpolated_code,
            row.quality,
            today,
        )
        cursor.execute(
            """
            INSERT OR IGNORE INTO daily_rainfall (id, station_id, date, rainfall, interpolated_code, quality, date_added)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )
        cursor.execute(
            """
            UPDATE daily_rainfall SET rainfall = ?, interpolated_code = ?, quality = ?, date_added = ? WHERE id = ?
            """,
            (row.rainfall, row.interpolated_code, row.quality, today, db_id),
        )
    conn.commit()


def load_rainfall_from_db(station_id, conn, **kwargs):
    """Read rainfall data from database.

    Args:
        station_id (str)
        conn (sqlite3.Connection)

    Returns:
        ausweather.RainfallStationData

    """
    cursor = conn.cursor()
    df = pd.read_sql(
        f"select * from daily_rainfall where station_id = '{station_id}'", conn
    )
    df["date"] = pd.to_datetime(df.date)
    df["year"] = df.date.dt.year
    df["dayofyear"] = df.date.dt.dayofyear
    df["finyear"] = [ausweather.date_to_finyear(d) for d in df["date"]]
    return ausweather.RainfallStationData.from_data(station_id, df, **kwargs)
