import pandas as pd

from finter.framework_model.content import Loader


class DisclosureLoader(Loader):
    def __init__(self, cm_name):
        self.__CM_NAME = cm_name
        self.__FREQ = cm_name.split(".")[-1]
        self.__ITEM_NAME = cm_name.split(".")[-2]

    def get_df(self, start: int, end: int, adj=True, fill_nan=True, unpivot=False, *args, **kwargs):
        raw = self._load_cache(
            self.__CM_NAME,
            start,
            end,
            freq=self.__FREQ,
            cache_t="hdf",
            fill_nan=fill_nan
        )
        
        if unpivot:
            if self.__ITEM_NAME != 'major_stock':
                pass
            else:
                s = raw.stack()
                s = s.apply(pd.Series)
                s = s.reset_index() 
                raw = s.rename(columns={'level_0':'datetime'})

        return raw
