import logging

import ausweather
from shapely.geometry import Point
import geopandas as gpd
from pydantic import BaseModel

from dew_gwdata import sageodata as connect_to_sageodata

logger = logging.getLogger(__name__)


class RainfallStations(BaseModel):
    station_id: str = ""

    station_name: str = ""

    nearest_to_well: str = ""
    sagd_env: str = "prod"

    def find_stations(self):
        sagd_db = connect_to_sageodata(service_name=self.sagd_env)

        sites = ausweather.get_sa_rainfall_site_list().sort_values("station_name")

        stations = None

        # Group 1 - search by job number range
        if self.station_id:
            df = sites[sites.station_id == self.station_id]
            title = f"Station ID {self.station_id}"
            query_params = [
                f"station_id={self.station_id}",
            ]
        elif self.station_name:
            df = sites[sites.station_name.str.contains(self.station_name, case=False)]
            title = f"Station name contains '{self.station_name.upper()}'"
            query_params = [f"station_name={self.station_name}"]

        elif self.nearest_to_well:
            well_id = sagd_db.find_wells(self.nearest_to_well).iloc[0]
            well_df = sagd_db.drillhole_details([well_id.dh_no])
            lat = well_df.iloc[0].latitude
            lon = well_df.iloc[0].longitude
            well_point = Point(lon, lat)
            gsites = gpd.GeoDataFrame(
                sites,
                geometry=gpd.points_from_xy(sites.lon, sites.lat),
                crs="epsg:7844",
            )
            gsites = gsites.to_crs("epsg:8059")
            wpoint = gpd.GeoDataFrame(
                {"geometry": [well_point] * len(gsites)}, crs="epsg:7844"
            )
            wpoint = wpoint.to_crs("epsg:8059")
            gsites["distance_km"] = (gsites.distance(wpoint) / 1000).round(3)
            df = gsites.sort_values("distance_km")
            title = f"Stations nearest '{well_id.unit_hyphen}'"
            query_params = [
                f"nearest_to_well={self.nearest_to_well}",
                f"sagd_env={self.sagd_env}",
            ]

        else:
            df = sites
            title = f"No search - all results returned"
            query_params = [
                f"station_id=0",
            ]

        return df, title, "&".join(query_params)
