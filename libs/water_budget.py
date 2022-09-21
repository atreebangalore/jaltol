from msilib import sequence
import os
import pandas as pd
from datetime import datetime
from datetime import timedelta as td
from calendar import monthrange
from typing import List, Dict, Tuple, Union
from.crop_details import kc_dict, crop_period
from .dynamic_world import DW
from .geeassets import iCol
import ee
ee.Initialize()

class CropDetails:
    def __init__(self, year: int, state: str, dist: str, season: Union[str, List[str]], geometry: ee.Geometry) -> None:
        self.geometry = geometry
        self.year = year
        self.state_n = state.upper()
        self.dist_n = dist.upper()
        self.season = season.split() if type(season)==str else season
    
    def get_crop_details(self, num_crops: int) -> Dict[str, Tuple[float, int, str, List[float], List[int]]]:
        output = {}
        seasonal_dict = {
            'Kharif': (6, 9),
            'Rabi': (10, 1),
            'Summer': (2, 5)
        }
        for season in self.season:
            lulc = DW(self.year, self.geometry)
            historical = lulc.get_historical(5)
            start, end = seasonal_dict[season]
            seasonal = lulc.get_seasonal(start, end, historical)
            # crops class - label = 4
            # https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1
            area_lulc = lulc.get_area_ha(4, seasonal)
            sowing_date = self.get_sowing_date(season)
            df = self.read_crop_details(season)
            df = df.sort_values(by=['perc'], ascending=False).head(num_crops).reset_index(drop=True)
            df['area_lulc'] = df['perc']*area_lulc
            for _ , row in df.iterrows():
                output[row['crop']] = (
                    row['area_lulc'],
                    row['perc'],
                    sowing_date,
                    self.get_kc_list(row['crop']),
                    self.get_period(row['crop']))
        return output
    
    def read_crop_details(self, season: str) -> pd.DataFrame:
        pkl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'data','crop_details')
        csv = pd.read_pickle(os.path.join(pkl_path, f'{self.state_n}.pkl.zip'))
        return csv[(csv['district'] == self.dist_n) & (csv['season'] == season) & (csv['perc'] != 0)]
    
    def get_sowing_date(self, season: str) -> str:
        sowing_dict = {
            'Kharif': f'{self.year}-06-01',
            'Rabi': f'{self.year}-10-01',
            'Summer': f'{self.year}-02-01'
        }
        return sowing_dict[season]

    def get_kc_list(self, crop: str) -> List[float]:
        return kc_dict[crop]
    
    def get_period(self, crop: str) -> List[int]:
        return crop_period[crop]

class CWR:
    def __init__(self, year: int, crop_details: Dict[str, Tuple[float, int, str, List[float], List[int]]]) -> None:
        self.year = year
        self.crop_dict = crop_details # {crop: (area_ha, area%, sowing date, Kc, period)}
    
    def get_refET(self, geometry: ee.Geometry) -> Dict[str,float]:
        EToCol = iCol['refET']
        self.ETo_dict = {} # {month: ETo}
        monthyearseq = self.mo_yr_seq(self.year)
        for period in monthyearseq:
            y, m = period
            image = EToCol.filterDate(ee.Date.fromYMD(y, m ,1).getRange('month')).first()
            self.ETo_dict[f'{m:02d}'] = image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geometry,
                scale=30,
                maxPixels=1e10
            ).getInfo()['b1']
        return self.ETo_dict
    
    def get_Kc_monthly(self) -> Dict[str, Dict[str, float]]:
        self.crop_monthly_kc = {} # {crop: {month: Kc}}
        for crop in self.crop_dict:
            monthdict = {f"{item:02d}": [] for item in range(1, 13)}
            area, p, start_date, crop_kc, crop_period = self.crop_dict[crop]
            start_date = datetime.strptime(start_date,"%Y-%m-%d")
            for stage in range(len(crop_kc)):
                end_date = start_date+td(days=crop_period[stage])
                date_range = pd.date_range(start_date, end_date)
                for idate in date_range:
                    monthdict[idate.strftime("%m")].append(crop_kc[stage])
                start_date = end_date + td(days=1)
            monthlyKc = {key: round(sum(value) / len(value), 2) for key, value in monthdict.items() if value}
            self.crop_monthly_kc[crop]=monthlyKc
        return self.crop_monthly_kc
    
    def get_ETc(self) -> Dict[str, float]:
        self.ETc_dict = {}
        mo_dy_dict = self.mo_range(self.year)
        for crop in self.crop_dict:
            ETc_list = []
            area, p, start_date, crop_kc, crop_period = self.crop_dict[crop]
            for month in self.crop_monthly_kc[crop]:
                ETc_month = self.crop_monthly_kc[month]*self.ETo_dict[month]*mo_dy_dict[month]*(p/100)
                ETc_list.append((ETc_month))
            self.ETc_dict[crop] = (sum(ETc_list) * area * 10) # mm*Ha -> m3
        return self.ETc_dict # {crop: ETc(m3)}
    
    def mo_yr_seq(self, year: int) -> List[Tuple[int, int]]:
        monthseq = list(range(6,13)) + list(range(1,6))
        yearseq = [year]*7 + [year+1]*5
        return [*zip(yearseq,monthseq)]
    
    def mo_range(self, year: int) -> Dict[str, int]:
        seq = self.mo_yr_seq(year)
        mr_dict = {}
        for ele in seq:
            yr, mo = ele
            _, days = monthrange(yr, mo)
            mr_dict[f"{mo:02d}"] = days
        return mr_dict # {month: no_of_days}