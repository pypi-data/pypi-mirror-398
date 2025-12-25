from pathlib import Path

import geopandas as gpd


class Spreadsheets:
    def __init__(self, cache=True):
        self.cache = cache

    def refresh(self):
        """Refresh cached versions of big spreadsheets."""
        for k in dir(self):
            if k.startswith("_cached"):
                del self.__dict__[k]
            _ = getattr(self, k)


def smustafa_confined_SE_T():
    """Read confined SE aquifer transmissivities from
    shapefile originally created by Keith Brown, now
    maintained by Saad Mustafa.

    """
    path = (
        Path(r"R:\DFW_Regional")
        / "MtGambier_ShareData"
        / "Groundwater"
        / "DWR (DWLBC GRASE)"
        / "Hydrogeological assessments"
        / "GIS_shape_files"
        / "Aquifer Properties and conductivities"
    )
    filename = path / "TCSA_Aq_Pro.dbf"
    return gpd.read_file(filename)
