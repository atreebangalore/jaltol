"""Module for Dynamic World LULC processing

Returns:
    float: area of the required label
"""
from .geeassets import iCol
from typing import Optional
import ee
ee.Initialize()


class DW:
    """Dynamic World class lets to filter the LULC collection and calculate area
    for the required label over the filter season(months) and year
    """

    def __init__(self, year: int, geometry: ee.Geometry) -> None:
        self.year = year
        self.geometry = geometry
        self.dw = iCol['dw']

    def get_historical(self, year_step: int) -> ee.ImageCollection:
        """Get the past years of DW LULC images filtered

        Args:
            year_step (int): no of years history to filter

        Returns:
            ee.ImageCollection: Filtered DW collection
        """
        self.historical = self.dw.filterBounds(self.geometry).filterDate(ee.Date.fromYMD(
            self.year-year_step, 6, 1), ee.Date.fromYMD(self.year+1, 6, 1)).select('label')
        return self.historical

    def get_seasonal(self, start_month: int, end_month: int, 
                    dw_col: Optional[ee.ImageCollection] = None) -> ee.ImageCollection:
        """get the images in the specific month range of every year in the
        collection

        Args:
            start_month (int): images with timestamp above will be include
            end_month (int): images with timestamp below will be included
            dw_col (ee.ImageCollection, optional): Specify Image Collection 
                or by default Historical Image Collection. Defaults to None.

        Returns:
            ee.ImageCollection: Images of particular season for every year
        """
        if not dw_col:
            dw_col = self.historical
        self.seasonal = dw_col.filter(
            ee.Filter.calendarRange(start_month, end_month, 'month'))
        return self.seasonal

    def get_area_ha(self, label: int, dw_col: Optional[ee.ImageCollection] = None) -> float:
        """get area of the required label feature over the geometry in hectares

        Args:
            label (int): label of the required DW class
            dw_col (ee.ImageCollection, optional): Specify Image Collection or 
                by default Seasonal Image Collection. Defaults to None.

        Returns:
            float: area of the required class in hectares
        """
        if not dw_col:
            dw_col = self.seasonal
        label_col = dw_col.map(lambda x: x.eq(label))
        label_sum = label_col.sum()
        label_fil = label_sum.gt(0)
        area_image = label_fil.multiply(ee.Image.pixelArea())
        area = area_image.reduceRegion(reducer=ee.Reducer.sum(
        ), geometry=self.geometry, scale=10, maxPixels=1e10)
        self.area_ha = ee.Number(area.get('label')).divide(1e4).getInfo()
        del label_col, label_fil, label_sum, area_image, area
        return self.area_ha
