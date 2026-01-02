from finter.framework_model.content import Loader
import pandas as pd
from finter.rest import ApiException


class BinancePriceVolumeLoader(Loader):   
    def __init__(self, cm_name):
        self.__CM_NAME = cm_name
        self.__FREQ = cm_name.split(".")[-1]

    def get_df(self, start: int, end: int, fill_nan=True, columns=None, *args, **kwargs):
        start_dt = pd.to_datetime(str(start))
        end_dt = pd.to_datetime(str(end))
        cm_name = self.__CM_NAME

        raw = self._load_cache(
            cm_name,
            start,
            end,
            universe="binance-all-spot",
            freq=self.__FREQ,
            fill_nan=fill_nan,
            columns=columns,
            *args,
            **kwargs
        )

        return raw
