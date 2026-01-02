import numpy as np
import pandas as pd

from finter.framework_model.content import Loader
from finter.settings import get_api_client, logger


class ClassificationLoader(Loader):
    def __init__(self, cm_name):
        self.__CM_NAME = cm_name
        self.__FREQ = cm_name.split(".")[-1]

    def get_df(
        self,
        start: int,
        end: int,
        quantit_universe=True,
        fill_nan=True,
        currency=None,
        stock_level=False,
        *args,
        **kwargs,
    ):
        raw = self._load_cache(
            self.__CM_NAME,
            start,
            end,
            universe="us-compustat-stock",
            freq=self.__FREQ,
            fill_nan=fill_nan,
            *args,
            **kwargs,
        )

        # Fix float32 precision issue: convert to float64 and round to nearest 5
        # (e.g., 35101008 → 35101010, 20106016 → 20106015)
        raw = (np.round(raw.astype(np.float64) / 5) * 5).astype(float)

        univ = self._load_cache(
            "content.spglobal.compustat.universe.us-stock-constituent.1d",
            start,  # to avoid start dependency in dataset
            end,
            universe="us-compustat-stock",
            freq=self.__FREQ,
            fill_nan=fill_nan,
            *args,
            **kwargs,
        )

        # stock_level을 위해 원본 컬럼 저장 (gvkey-IID 형태)
        univ_original_columns = univ.columns.tolist()

        # 컬럼명을 중복되지 않게 처리
        univ.columns = [col[:-2] for col in univ.columns]

        # 중복된 컬럼들을 그룹화하여 최대값 계산
        univ = univ.groupby(univ.columns, axis=1).max()

        # 필터 적용
        if quantit_universe:
            raw = raw.loc[univ.index[0] :] * univ
        else:
            self.client = get_api_client()
            if self.client.user_group != "quantit":
                raise AssertionError("Only quantit user group can use all universe")

        raw = raw.replace(0, np.nan)

        # stock_level=True인 경우 security level로 broadcasting
        if stock_level:
            # universe의 원본 컬럼(gvkey-IID)을 활용하여 broadcasting
            raw_broadcasted = {}
            for orig_col in univ_original_columns:
                # 원본 컬럼에서 gvkey 추출 (앞 6자리)
                gvkey = orig_col[:6]
                if gvkey in raw.columns:
                    raw_broadcasted[orig_col] = raw[gvkey]

            # DataFrame으로 변환
            raw = pd.DataFrame(raw_broadcasted, index=raw.index)
        else:
            # stock_level=False: company level 데이터 반환
            logger.warning(
                "[ClassificationLoader] Returning company-level data (gvkey only). "
                "If you want to merge with stock-level data (price/volume), "
                "please set 'stock_level=True' to broadcast to security level (gvkey-IID)."
            )

        return raw
