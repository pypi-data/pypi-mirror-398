from datetime import datetime

import numpy as np
import pandas as pd
from finter.framework_model.content import Loader

initial_date = 20191230


class FinancialLoader(Loader):
    def __init__(self, cm_name):
        self.__CM_NAME = cm_name
        self.__FREQ = cm_name.split(".")[-1]

    @staticmethod
    def _unpivot_df(raw):
        unpivot_df = raw.unstack().dropna().reset_index()
        unpivot_df.columns = ["id", "pit", "val"]
        m = (
            pd.DataFrame([*unpivot_df["val"]], unpivot_df.index)
            .stack()
            .rename_axis([None, "fiscal"])
            .reset_index(1, name="value")
        )
        result = unpivot_df[["id", "pit"]].join(m)
        return result.dropna(subset=["fiscal", "value"])

    def get_df(
        self,
        start: int,
        end: int,
        fill_nan=True,
        mode = None,
        *args,
        **kwargs
    ):
        """
        unpivot : None, 'unpivot'
        """
        raw = self._load_cache(
            self.__CM_NAME,
            initial_date,
            end,
            freq=self.__FREQ,
            fill_nan=fill_nan,
            cache_t="hdf",
        )

        raw = raw.loc[
            datetime.strptime(str(start), "%Y%m%d") : datetime.strptime(
                str(end), "%Y%m%d"
            )
        ]
        
        if mode == 'unpivot':
            raw = raw.dropna(how="all")
            raw = FinancialLoader._unpivot_df(raw)
        return raw
