import os
import pandas as pd
from datetime import date
from datetime import timedelta as td
from typing import List, Dict, Tuple, Union
from.crop_details import kc_dict, crop_period
from .dynamic_world import DW
import ee
ee.Initialize()

class CropDetails:
    def __init__(self, year: int, state: str, dist: str, season: Union[str, List[str]], geometry: ee.Geometry) -> None:
        self.geometry = geometry
        self.year = year
        self.state_n = state.upper()
        self.dist_n = dist.upper()
        if type(season) == str:
            self.season = season.split()
        elif type(season) == list:
            self.season = season
        else:
            raise TypeError(f'season({type(season)}) - expected str or list type')
    
    def get_crop_details(self, num_crops: int) -> Dict[str, Tuple[float, str, List[float], List[int]]]):
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
    def __init__(self, year: int, crop_details: Dict[str, Tuple[float, str, List[float], List[int]]]) -> None:
        pass