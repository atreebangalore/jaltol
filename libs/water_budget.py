from typing import List, Dict, Tuple, Union
import ee
ee.Initialize()

class CropDetails:
    def __init__(self, state: str, dist: str, season: Union[str, List]) -> None:
        pass

class CWR:
    def __init__(self, year: int, crop_details: Dict[str, Tuple[float, str, List, List]]) -> None:
        pass