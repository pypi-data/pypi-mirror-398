import warnings

import pandas as pd

from finter.framework_model.content import Loader


class PriceVolumeLoader(Loader):
    def __init__(self, cm_name):
        self.__CM_NAME = cm_name
        self.__FREQ = cm_name.split(".")[-1]
        self.__ITEM = cm_name.split(".")[-2].split("-")[2]

    def get_df(
        self,
        start: int,
        end: int,
        adj=True,
        adj_div=False,
        fill_nan=True,
        *args,
        **kwargs,
    ) -> pd.DataFrame:
        base_args = {
            "start": start,
            "end": end,
            "universe": f"id-compustat-stock",
            "freq": self.__FREQ,
            "cache_t": "hdf",
            "fill_nan": fill_nan,
        }
        raw = self._load_cache(self.__CM_NAME, **{**base_args, **kwargs}).astype(float)

        if self.__ITEM in ["adjust_factor", "total_return_factor"]:
            return raw

        raw_col = raw.columns

        if adj:
            adj_cm_name = f"content.ticmi.api.price_volume.id-stock-adjust_factor.1d"

            adj_factor = (
                self._load_cache(adj_cm_name, **base_args)
                .reindex(columns=raw_col)
                .fillna(1)
            )

            if adj_div:
                total_return_factor = (
                    self._load_cache(
                        f"content.ticmi.api.price_volume.id-stock-total_return_factor.1d",
                        **base_args
                    )
                    .reindex(columns=raw_col)
                    .fillna(1)
                )
                adj_factor /= total_return_factor

            if self.__ITEM in ["stock_outstanding", "volume_sum"]:
                raw = raw * adj_factor
            elif self.__ITEM in [
                "price_open",
                "price_high",
                "price_low",
                "price_close",
            ]:
                raw = raw / adj_factor
            else:
                raise ValueError

            warnings.warn(
                f"\n{self.__CM_NAME.split('.')[-2]} has been adjusted. Use adj=False if you want unadjusted values"
            )
        return raw
