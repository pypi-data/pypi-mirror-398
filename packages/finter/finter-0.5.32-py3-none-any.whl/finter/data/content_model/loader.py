import fnmatch
from pathlib import Path

import yaml
from cachetools import TTLCache

from finter import BaseAlpha
from finter.api.content_api import ContentApi
from finter.calendar import iter_days, iter_trading_days
from finter.data.content_model.catalog_sheet import get_data
from finter.data.content_model.financial_calculator import FinancialCalculator
from finter.data.content_model.usage import (
    CONTENTFACTORY_GENERAL_USAGE_TEXT,
    get_standard_item_usage,
)
from finter.data.fin_helper import FinHelper
from finter.framework_model.aws_credentials import get_parquet_info
from finter.settings import get_api_client, logger


class ContentFactory:
    """
    A class representing a content model (CM) factory that generates and manages content models
    based on a specified universe name and a time range.

    Attributes:
        start (int): Start date for the content in YYYYMMDD format.
        end (int): End date for the content in YYYYMMDD format.
        universe_name (str): Name of the universe to base content models on.
        match_list (list[str]): Patterns used to match content models based on the universe name.
        cm_dict (dict[str, list[str]]): Dictionary mapping content match patterns to lists of corresponding content model names.

    Methods:
        get_df(item_name: str) -> pd.DataFrame:
            Retrieves the DataFrame associated with a specified item name.
        get_fc(item: str | dict) -> FinancialCalculator:
            Retrieves FinancialCalculator instance for fluent API data transformations.
            Single item: returns FC instance. Multiple items: auto-joins and returns FC instance.
        get_full_cm_name(item_name: str) -> str:
            Retrieves the full content model name for a specified item name.
        determine_base() -> list[str]:
            Determines the base match patterns for content models based on the universe name.
        get_cm_dict() -> dict:
            Generates the content model dictionary based on the universe's match list.
        show():
            Displays an interactive widget for exploring content model information in a scrollable list format.

    Property:
        item_list (list[str]): Provides a sorted list of unique item names from the content model dictionary.
    """

    # 클래스 레벨 캐시
    _global_cache = None
    _metadata_cache = {}  # universe_name -> metadata dict
    _code_map_cache = {}  # code_map_name -> code_map dict

    # universe별 item alias 매핑 (실제이름 -> 표시이름)
    _display_alias_map = {
        "kr_stock": {
            "kr_px_last": "market_indicator",
        },
        "us_stock": {
            "us_px_last": "market_indicator",
        },
        "us_etf": {
            "us_px_last": "market_indicator",
        },
        "vn_stock": {
            "vnm_px_last": "market_indicator",
        },
        "id_stock": {
            "idn_px_last": "market_indicator",
        },
    }

    @classmethod
    def _load_metadata(cls, universe_name):
        """Load item metadata from YAML file for specific universe."""
        if universe_name not in cls._metadata_cache:
            metadata_path = Path(__file__).parent / "metadata" / f"{universe_name}.yaml"
            if metadata_path.exists():
                with open(metadata_path, "r", encoding="utf-8") as f:
                    cls._metadata_cache[universe_name] = yaml.safe_load(f) or {}
            else:
                cls._metadata_cache[universe_name] = {}
        return cls._metadata_cache[universe_name]

    @classmethod
    def _load_code_map(cls, name):
        """Load code map from YAML file."""
        if name not in cls._code_map_cache:
            code_map_path = (
                Path(__file__).parent / "metadata" / "code_maps" / f"{name}.yaml"
            )
            if code_map_path.exists():
                with open(code_map_path, "r", encoding="utf-8") as f:
                    cls._code_map_cache[name] = yaml.safe_load(f) or {}
            else:
                cls._code_map_cache[name] = {}
        return cls._code_map_cache[name]

    def get_description(self, item_name):
        """
        Get description and note for an item.

        Args:
            item_name: Item name

        Returns:
            tuple: (description, note) or (str, None) for flat structure
        """
        metadata = self._load_metadata(self.universe_name)
        value = metadata.get(item_name)
        if value is None:
            return None, None
        if isinstance(value, dict):
            return value.get("description"), value.get("note")
        return value, None

    def code_map(self, name, level=1):
        """
        Get code map for an item.

        Args:
            name (str): Code map name (e.g., 'gics', 'idxic')
            level (int): Hierarchy level
                For GICS:
                    1: Sector (2-digit, 11 items)
                    2: Industry Group (4-digit, 27 items)
                    3: Industry (6-digit, 84 items)
                    4: Sub-Industry (8-digit, 215 items)
                    0: All levels (337 items)
                For IDXIC (IDX Industrial Classification):
                    1: Sector (12 items)
                    2: Group (68 items)
                    3: Industry (129 items)
                    0: All levels (209 items)

        Returns:
            pd.DataFrame: Code map with code and description

        Example:
            cf.code_map('gics')           # Sector (default)
            cf.code_map('gics', level=2)  # Industry Group
            cf.code_map('gics', level=0)  # All
            cf.code_map('idxic')            # IDX Sector
            cf.code_map('idxic', level=3)  # IDX Industry
        """
        import pandas as pd

        from finter.data import QuandaData

        if name == "gics":
            data = QuandaData.get("spglobal/gics/map")
            df = pd.DataFrame(eval(data))
            df = df.rename(
                columns={
                    "giccd": "code",
                    "gicdesc": "description",
                    "gicstat": "status",
                    "gictype": "type",
                }
            )
            df = df.sort_values("code")

            # Filter by level
            level_map = {
                1: "GSECTOR",  # Sector
                2: "GGROUP",  # Industry Group
                3: "GIND",  # Industry
                4: "GSUBIND",  # Sub-Industry
            }
            if level != 0:
                gictype = level_map.get(level, "GSECTOR")
                df = df[df["type"] == gictype]

            return df.set_index("code")[["description", "type", "status"]]

        if name == "idxic":
            code_map = self._load_code_map("idxic")
            if not code_map:
                raise ValueError("Code map 'idx' not found.")

            rows = []
            for code, value in code_map.items():
                rows.append(
                    {
                        "code": code,
                        "description": value.get("description", ""),
                        "type": value.get("type", ""),
                        "idx_code": value.get("idx_code", ""),
                    }
                )
            df = pd.DataFrame(rows).sort_values("code")

            # Filter by level
            level_map = {
                1: "SECTOR",
                2: "GROUP",
                3: "INDUSTRY",
            }
            if level != 0:
                idx_type = level_map.get(level, "SECTOR")
                df = df[df["type"] == idx_type]

            return df.set_index("code")[["description", "type", "idx_code"]]

        # Fallback to yaml file
        code_map = self._load_code_map(name)
        if not code_map:
            raise ValueError(f"Code map '{name}' not found.")
        return pd.DataFrame(
            list(code_map.items()), columns=["code", "description"]
        ).set_index("code")

    def __init__(
        self,
        universe_name: str,
        start: int,
        end: int,
        cache_timeout: int = 0,
        cache_maxsize: int = 10,
        sub_universe=None,  # : Optional[list | pd.DataFrame]
        backup_day=None,  # bool or YYYYMMDD for daily backup file; max backup_day is before 14 days
    ):
        """
        Initializes the ContentFactory with the specified universe name, start date, and end date.

        Args:
            universe_name (str): The name of the universe which the content models are based on.
                Example: 'raw', 'kr_stock'.
            start (int): The start date for the content in YYYYMMDD format.
                Example: 20210101.
            end (int): The end date for the content in YYYYMMDD format.
                Example: 20211231.
            cache_timeout (int): The number of seconds after which the cache expires.
                Example: 3600 (1 hour).
            cache_maxsize (int): The maximum number of items to store in the cache.
                Example: 1000.
            sub_universe (Optional[list | pd.DataFrame]): A list or DataFrame of sub-universe items.

        Raises:
            ValueError: If the universe name is not supported.
        """
        self.client = get_api_client()
        self.start = start
        self.end = end
        self.universe_name = universe_name
        self.sub_universe = sub_universe
        self.backup_day = backup_day
        self.api_instance = ContentApi(self.client)

        self.gs_df = get_data(content_api=self.api_instance)
        self.us_gs_df = None

        self.match_list = self.determine_base()
        self.cm_dict = self.get_cm_dict()

        self.trading_days = self.get_trading_days(start, end, universe_name)

        if cache_timeout > 0:
            self.use_cache = True
        else:
            self.use_cache = False

        if self.use_cache and ContentFactory._global_cache is None:
            ContentFactory.initialize_cache(maxsize=cache_maxsize, ttl=cache_timeout)

    def _get_us_gs_df(self):
        if self.us_gs_df is None:
            self.us_gs_df = get_data(
                content_api=self.api_instance, cm_type="us_financial"
            )
        return self.us_gs_df

    @staticmethod
    def get_trading_days(start, end, universe_name):
        if universe_name in ["kr_stock"]:
            return sorted(iter_trading_days(start, end, exchange="krx"))
        elif universe_name in ["us_stock", "us_etf", "us", "us_future"]:
            return sorted(iter_trading_days(start, end, exchange="us"))
        elif universe_name in ["vn_stock"]:
            return sorted(iter_trading_days(start, end, exchange="vnm"))
        elif universe_name in ["id_stock", "id_fund", "id_bond"]:
            return sorted(iter_trading_days(start, end, exchange="id"))
        # TODO: [TEMP] crypto_test - 테스트용, 정식 배포 시 제거
        elif universe_name == "crypto_test":
            return sorted(iter_days(start, end))
        else:
            logger.info(f"Unsupported universe: {universe_name}, All days are returned")
            return sorted(iter_days(start, end))

    # Todo: Migrate universe with db or gs sheet or ...
    def determine_base(self):
        def __match_data(u):
            df = self.gs_df
            return list(df[df["Universe"] == u]["Object Path"])

        if self.universe_name == "raw":
            return []
        elif self.universe_name == "kr_stock":
            return __match_data("KR STOCK")
        elif self.universe_name == "us_etf":
            return __match_data("US ETF")
        elif self.universe_name == "us_stock":
            return __match_data("US STOCK")
        elif self.universe_name == "us":
            return __match_data("US")
        elif self.universe_name == "us_future":
            return __match_data("US FUTURE")
        elif self.universe_name == "vn_stock":
            return __match_data("VN STOCK")
        elif self.universe_name == "id_stock":
            return __match_data("ID STOCK")
        elif self.universe_name == "id_bond":
            return __match_data("ID BOND")
        elif self.universe_name == "id_fund":
            return __match_data("ID FUND")
        elif self.universe_name == "crypto_spot":
            return __match_data("CRYPTO SPOT")
        elif self.universe_name == "crypto_future":
            return __match_data("CRYPTO FUTURE")
        elif self.universe_name == "btcusdt_spot_binance":
            return __match_data("BTCUSDT SPOT BINANCE")
        elif self.universe_name == "btcusdt_future_binance":
            return __match_data("BTCUSDT FUTURE BINANCE")
        elif self.universe_name == "common":
            return __match_data("COMMON")
        # TODO: [TEMP] crypto_test - 테스트용, 정식 배포 시 제거
        elif self.universe_name == "crypto_test":
            return ["content.crypto.bnp_usdt.*.600"]
        else:
            raise ValueError(f"Unknown universe: {self.universe_name}")

    def get_cm_dict(self):
        if self.universe_name == "raw":
            return {}

        # TODO: [TEMP] crypto_test - 테스트용, 정식 배포 시 제거
        if self.universe_name == "crypto_test":
            return {
                ("content.crypto.bnp_usdt.*.600", "Price", "10min"): ["close"],
            }

        cm_dict = {}
        for match in self.match_list:
            api_category = self.gs_df[self.gs_df["Object Path"] == match][
                "Category"
            ].tolist()[0]
            api_sub_category = self.gs_df[self.gs_df["Object Path"] == match][
                "Sub Category"
            ].tolist()[0]

            cm_name_category = match.split(".")[3]
            try:
                cm_list = self.api_instance.content_identities_retrieve(
                    category=cm_name_category
                ).cm_identity_name_list

                net_cm_list = [
                    item.split(".")[4]
                    for item in cm_list
                    if fnmatch.fnmatchcase(item, match)
                ]
                if self.universe_name == "us_etf":
                    if api_category == "Economic":
                        pass  # Economic/Indicator 카테고리는 필터링 건너뛰기
                    else:
                        net_cm_list = [
                            cm.replace("us-etf-", "")
                            for cm in net_cm_list
                            if "us-etf" in cm
                        ]
                elif self.universe_name == "us":
                    net_cm_list = [
                        cm.replace("us-all-", "")
                        for cm in net_cm_list
                        if "us-all" in cm
                    ]
                elif self.universe_name == "us_future":
                    pass
                elif self.universe_name == "us_stock":
                    if cm_name_category in [
                        "price_volume",
                        "classification",
                        "universe",
                    ]:
                        net_cm_list = [
                            cm.replace("us-stock-", "")
                            for cm in net_cm_list
                            if "us-stock-" in cm
                        ]
                    elif cm_name_category == "financial":
                        if self.client.user_group != "quantit":
                            self.us_gs_df = self._get_us_gs_df()
                            identity_format = match.split(".")[4]
                            if identity_format[-2] == "-":
                                net_cm_list = list(self.us_gs_df["items"].values)
                            elif identity_format[-2] == "_":
                                net_cm_list = list(self.us_gs_df["pit_items"].values)
                        else:
                            self.us_gs_df = self._get_us_gs_df()
                            identity_format = match.split(".")[4]
                            if identity_format[-2] == "-":
                                net_cm_list = [
                                    cm.replace("us-stock-", "") for cm in net_cm_list
                                ]
                            elif identity_format[-2] == "_":
                                net_cm_list = [
                                    cm.replace("us-stock_", "") for cm in net_cm_list
                                ]
                    elif cm_name_category == "factor":
                        net_cm_list = [
                            cm.replace("us-stock_pit-", "")
                            for cm in net_cm_list
                            # if "us-stock_pit-" in cm
                        ]
                elif self.universe_name == "vn_stock":
                    net_cm_list = [
                        cm.replace("vnm-stock-", "") if "vnm-stock" in cm else cm
                        for cm in net_cm_list
                    ]
                elif self.universe_name == "id_stock":
                    net_cm_list = [
                        cm.replace("id-stock-", "") if "id-stock-" in cm else cm
                        for cm in net_cm_list
                    ]
                elif self.universe_name == "id_bond":
                    net_cm_list = [
                        cm.replace("bond-", "") if "bond-" in cm else cm
                        for cm in net_cm_list
                    ]
                elif self.universe_name == "id_fund":
                    net_cm_list = [
                        cm for cm in net_cm_list if not cm.startswith("bond-")
                    ]
                elif self.universe_name == "crypto_spot":
                    net_cm_list = [
                        cm.replace("spot-", "") if "spot-" in cm else cm
                        for cm in net_cm_list
                        if not cm.split("_")[-1].isdigit()
                    ]
                elif self.universe_name == "crypto_future":
                    net_cm_list = [
                        cm
                        for cm in net_cm_list
                        if not cm.split("_")[-1].isdigit() and "_m" in cm
                    ]
                elif self.universe_name == 'btcusdt_spot_binance':
                    net_cm_list = [
                        cm.replace("btcusdt-spot-", "") if "spot-" in cm else cm
                        for cm in net_cm_list
                        if not cm.split("_")[-1].isdigit()
                    ]
                elif self.universe_name == 'btcusdt_future_binance':
                    net_cm_list = [
                        cm.replace("btcusdt-usd_m-", "") if "_m" in cm else cm
                        for cm in net_cm_list
                        if not cm.split("_")[-1].isdigit()
                    ]

                # 표시용 alias 적용 (실제이름 -> 표시이름)
                if self.universe_name in self._display_alias_map:
                    alias = self._display_alias_map[self.universe_name]
                    net_cm_list = [alias.get(cm, cm) for cm in net_cm_list]

                cm_dict[match, api_category, api_sub_category] = net_cm_list
            except Exception as e:
                logger.error(f"API call failed: {e}")
        return cm_dict

    def get_df(self, item_name, category=None, freq="1d", **kwargs):
        cm_name = self.get_full_cm_name(item_name, category, freq)
        param = {
            "start": self.start,
            "end": self.end,
            "sub_universe": self.sub_universe,
            "backup_day": self.backup_day,
        }
        if self.sub_universe is None:
            param.pop("sub_universe")
        param.update(kwargs)
        if self.client.user_group in ["free_tier", "data_beta"]:
            param["code_format"] = "short_code"
            param["trim_short"] = True
            if "ftp.financial" in cm_name or "ftp.consensus" in cm_name:
                param["code_format"] = "cmp_cd"

        if self.use_cache and ContentFactory._global_cache is not None:
            cache_key = (cm_name, frozenset(param.items()))
            if cache_key in ContentFactory._global_cache:
                return ContentFactory._global_cache[cache_key]

        df = BaseAlpha.get_cm(cm_name).get_df(**param)
        if self.use_cache and ContentFactory._global_cache is not None:
            ContentFactory._global_cache[cache_key] = df

        return df

    def get_fc(self, item, **kwargs):
        """
        Get FinancialCalculator instance (long format).

        ⚠️  Only works with Financial category items (items with dict values containing fiscal periods).

        Args:
            item: Single item name (str) or multiple items (dict)
                  - str: "krx-spot-total_assets"
                  - dict: {"assets": "krx-spot-total_assets",
                           "current": "krx-spot-current_assets"}
            **kwargs: Additional parameters for get_df (e.g., quarters, category, freq)

        Returns:
            FinancialCalculator instance (long format)

        Raises:
            ValueError: If item is not in Financial category

        Examples:
            # Single item
            assets = cf.get_fc('krx-spot-total_assets')
            assets.to_wide()

            # Multiple items (auto join)
            result = cf.get_fc({
                'assets': 'krx-spot-total_assets',
                'current': 'krx-spot-current_assets'
            }).apply_expression("assets - current").to_wide()

            # With filtering
            result = cf.get_fc({
                'assets': 'krx-spot-total_assets',
                'current': 'krx-spot-current_assets'
            }).filter(pl.col("id") == 12170).apply_expression("assets - current")
        """
        # Validate category for all items
        items_to_check = [item] if isinstance(item, str) else list(item.values())

        for item_name in items_to_check:
            category = kwargs.get("category")
            freq = kwargs.get("freq", "1d")

            # Get cm_name to find category
            cm_name = self.get_full_cm_name(item_name, category, freq)

            # Find category from cm_dict
            item_category = None
            for key, items in self.cm_dict.items():
                if item_name in items:
                    item_category = key[1]  # api_category
                    break

            # Check if it's a financial category
            if item_category and "financial" not in item_category.lower():
                raise ValueError(
                    f"get_fc() only works with Financial category items.\n"
                    f"Item '{item_name}' is in category '{item_category}'.\n"
                    f"Use cf.get_df('{item_name}') instead for non-financial data."
                )

        # All items validated, proceed with creation
        # Get id_table for us_stock (for gvkey -> gvkeyiid mapping in to_wide)
        id_table = (
            FinHelper.get_id_table() if self.universe_name == "us_stock" else None
        )

        # Load from fixed initial date for path-independent cummax_fiscal calculation
        # The final output will be filtered by trading_days in to_wide()
        initial_date = 20000101

        if isinstance(item, str):
            # Single item: return FC instance
            # us_stock pit data: use mode='original' for dict format with fiscal
            if self.universe_name == "us_stock" and item.startswith("pit-"):
                kwargs.setdefault("mode", "original")
            kwargs["start"] = initial_date
            df = self.get_df(item, **kwargs)
            return FinancialCalculator(
                df, trading_days=self.trading_days, id_table=id_table
            )
        elif isinstance(item, dict):
            # Multiple items: auto join
            fcs = {}
            for name, item_name in item.items():
                item_kwargs = kwargs.copy()
                # us_stock pit data: use mode='original' for dict format with fiscal
                if self.universe_name == "us_stock" and item_name.startswith("pit-"):
                    item_kwargs.setdefault("mode", "original")
                item_kwargs["start"] = initial_date
                fcs[name] = FinancialCalculator(
                    self.get_df(item_name, **item_kwargs),
                    trading_days=self.trading_days,
                    id_table=id_table,
                )
            return FinancialCalculator.join(fcs)
        else:
            raise TypeError(
                f"item must be str or dict, got {type(item).__name__}. "
                f"Examples: cf.get_fc('total_assets') or "
                f"cf.get_fc({{'assets': 'total_assets', 'current': 'current_assets'}})"
            )

    def to_security(self, df):
        """
        Broadcast company-level DataFrame to security-level DataFrame.

        Converts gvkey (6-digit company code) columns to gvkeyiid (8-9 digit security code) columns.
        Only applicable for us_stock universe.

        Args:
            df: DataFrame with gvkey columns (company-level, 6-digit)

        Returns:
            DataFrame with gvkeyiid columns (security-level, 8-9 digit)

        Raises:
            ValueError: If universe is not us_stock or if DataFrame already has security-level columns

        Example:
            df_company = cf.get_df("total_assets")  # gvkey columns
            df_security = cf.to_security(df_company)  # gvkeyiid columns
        """
        import pandas as pd

        if self.universe_name != "us_stock":
            raise ValueError(
                f"to_security() only supports us_stock universe. "
                f"Current universe: {self.universe_name}"
            )

        id_table = FinHelper.get_id_table()

        # Normalize column names to str with zero-padding (gvkey format)
        df_cols = {str(col).zfill(6): col for col in df.columns}

        # Validation: check if already security-level
        sample_col = list(df_cols.keys())[0]
        if sample_col in id_table["gvkeyiid"].values:
            raise ValueError(
                "DataFrame already has security-level columns (gvkeyiid). "
                "Expected company-level (6-digit gvkey)."
            )

        # Broadcast gvkey -> gvkeyiid
        result = {}
        for gvkey, gvkeyiid in zip(id_table["gvkey"], id_table["gvkeyiid"]):
            if gvkey in df_cols:
                result[gvkeyiid] = df[df_cols[gvkey]]

        return pd.DataFrame(result, index=df.index)

    def get_cm_info(self, item_name, category=None, freq="1d"):
        cm_name = self.get_full_cm_name(item_name, category, freq)
        return get_parquet_info(cm_name)

    # Todo: Dealing duplicated item name later
    def get_full_cm_name(self, item_name, category=None, freq="1d"):
        if self.universe_name == "raw":
            return item_name

        try:
            if "crypto_spot" in self.universe_name:
                cm_list = [
                    key[0].replace("*", "{}").format(*item_name.split("-"))
                    for key, items in self.cm_dict.items()
                    if item_name in items
                ]
            else:
                cm_list = [
                    key[0].replace("*", item_name)
                    for key, items in self.cm_dict.items()
                    if item_name in items
                ]

            if len(cm_list) > 1:
                logger.info(
                    f"""
                    Multiple matching cm are detected
                    Matching cm list : {str([cm_name.split(".")[3] + "." + item_name + "." + cm_name.split(".")[5] for cm_name in cm_list])}
                    """
                )
                if category is not None:
                    cm_list = [cm for cm in cm_list if category in cm]
                if freq != "1d":
                    cm_list = [cm for cm in cm_list if freq.lower() in cm]
                cm_name = cm_list[0]
                logger.info(
                    f"""
                    {cm_name.split(".")[3] + "." + item_name + "." + cm_name.split(".")[5]} is returned
                    To specify a different cm, use category or freq parameters.
                    For example, .get_df('SP500_EWS', freq = '1M')  \t .get_df('all-mat_cat_rate', category = 'sentiment_exp_us')
                    """
                )
                return cm_name
            else:
                return next(iter(cm_list))

        except StopIteration:
            raise ValueError(f"Unknown item_name: {item_name}")

    def show(self):
        from IPython.display import HTML, display

        # Build mappings for categories and subcategories
        category_mapping = {}
        subcategory_mapping = {}

        for key in self.cm_dict.keys():
            category = key[1]
            subcategory = key[2]
            freq = key[0].split(".")[-1]

            subcategory = f"{subcategory} ({freq})"

            if self.universe_name == "vn_stock":
                if "spglobal" in key[0]:
                    category = f"{category} (deprecated)"
                else:
                    category = category

            if "-v2" in key[0].split(".")[-3]:
                category = f"{category} (v2)"

            elif category_mapping.get(category):
                if self.universe_name == "us_stock" and category == "financial":
                    category = "PIT financial"

            # Initialize category and subcategory mappings
            if category not in category_mapping:
                category_mapping[category] = set()
            category_mapping[category].add(subcategory)

            if category not in subcategory_mapping:
                subcategory_mapping[category] = {}
            if subcategory not in subcategory_mapping[category]:
                subcategory_mapping[category][subcategory] = []
            subcategory_mapping[category][subcategory].extend(self.cm_dict[key])

        # Create sorted lists for dropdown options
        categories = sorted(category_mapping.keys())

        # 데이터 구조 생성
        import json

        data_structure = {}
        for category in categories:
            data_structure[category] = {}
            for subcategory in sorted(category_mapping[category]):
                items = subcategory_mapping[category][subcategory]

                # Find matching key
                matching_key = next(
                    key
                    for key in self.cm_dict.keys()
                    if key[1]
                    == category.replace(" (deprecated)", "")
                    .replace(" (v2)", "")
                    .replace("PIT ", "")
                    and key[2] == subcategory.split(" (")[0]
                )

                url = self.gs_df[self.gs_df["Object Path"] == matching_key[0]][
                    "URL"
                ].tolist()[0]

                data_structure[category][subcategory] = {"items": items, "url": url}

        # HTML + JavaScript로 구현
        html_content = f"""
        <div id="content-viewer">
            <div style="margin-bottom: 10px;">
                <div style="margin-bottom: 5px;">
                    <label>Category: </label>
                    <select id="category-select" style="padding: 5px;">
                        {"".join(f'<option value="{cat}">{cat}</option>' for cat in categories)}
                    </select>
                </div>
                <div>
                    <label>Subcategory: </label>
                    <select id="subcategory-select" style="padding: 5px;">
                    </select>
                </div>
            </div>
            <div id="content-display"></div>
        </div>
        
        <script>
        var dataStructure = {json.dumps(data_structure)};
        
        function updateSubcategories() {{
            var category = document.getElementById('category-select').value;
            var subcategorySelect = document.getElementById('subcategory-select');
            subcategorySelect.innerHTML = '';
            
            var subcategories = Object.keys(dataStructure[category]);
            subcategories.forEach(function(subcat) {{
                var option = document.createElement('option');
                option.value = subcat;
                option.text = subcat;
                subcategorySelect.appendChild(option);
            }});
            
            updateContent();
        }}
        
        function updateContent() {{
            var category = document.getElementById('category-select').value;
            var subcategory = document.getElementById('subcategory-select').value;
            var data = dataStructure[category][subcategory];
            
            var itemsList = data.items.map(function(item) {{
                return '<li>' + item + '</li>';
            }}).join('');
            
            var html = '<h3>' + category + ' - ' + subcategory + '</h3>' +
                    '<div style="height:600px;width:400px;border:1px solid #ccc;overflow:auto;float:left;margin-right:10px;">' +
                    '<ul>' + itemsList + '</ul></div>' +
                    '<iframe src="' + data.url + '" width="1000" height="600" style="float:left;"></iframe>' +
                    '<div style="clear:both;"></div>';
            
            document.getElementById('content-display').innerHTML = html;
        }}
        
        document.getElementById('category-select').addEventListener('change', updateSubcategories);
        document.getElementById('subcategory-select').addEventListener('change', updateContent);
        
        // Initialize
        updateSubcategories();
        </script>
        """

        display(HTML(html_content))

    @property
    def item_list(self):
        return sorted(
            set(item for sublist in self.cm_dict.values() for item in sublist)
        )

    @property
    def categories(self):
        """Get all available categories."""
        return sorted(set(key[1] for key in self.cm_dict.keys()))

    @property
    def subcategories(self):
        """Get all available subcategories."""
        return sorted(set(key[2] for key in self.cm_dict.keys()))

    def get_subcategories(self, category):
        """Get subcategories for a specific category."""
        return sorted(set(key[2] for key in self.cm_dict.keys() if key[1] == category))

    def get_items_by_category(
        self, category=None, subcategory=None, exclude_subcategory=None
    ):
        """Get items filtered by category and/or subcategory.

        Args:
            category (str, optional): Filter by category (exact match)
            subcategory (str, optional): Filter by subcategory.
                - Exact match: "pit-1d"
                - Prefix match: "pit-*" (matches pit-1d, pit-1q, etc.)
            exclude_subcategory (str, optional): Exclude subcategories.
                - Exact match: "pit-1d"
                - Prefix match: "pit-*" (excludes all pit-* subcategories)
        """
        items = []
        for key, item_list in self.cm_dict.items():
            match_path, cat, subcat = key

            if category and cat != category:
                continue

            # Subcategory matching (supports prefix with *)
            if subcategory:
                if subcategory.endswith("*"):
                    prefix = subcategory[:-1]
                    if not subcat.startswith(prefix):
                        continue
                elif subcat != subcategory:
                    continue

            # Subcategory exclusion (supports prefix with *)
            if exclude_subcategory:
                if exclude_subcategory.endswith("*"):
                    prefix = exclude_subcategory[:-1]
                    if subcat.startswith(prefix):
                        continue
                elif subcat == exclude_subcategory:
                    continue

            items.extend(item_list)

        return sorted(set(items))

    def usage(self, item_name=None, category=None, freq="1d"):
        """
        Display usage information for a specific item or general get_df usage.

        Args:
            item_name (str, optional): The item name to show specific usage for.
                If None, shows general usage information.
            category (str, optional): Category filter when multiple matches exist.
            freq (str): Frequency filter (default: "1d").

        Example:
            cf = ContentFactory("kr_stock", 20230101, 20250101)

            # Show general usage
            cf.usage()

            # Show usage for specific item (if loader has special features)
            cf.usage("total_assets")
        """
        if item_name is None:
            # General usage
            print(CONTENTFACTORY_GENERAL_USAGE_TEXT)
        else:
            try:
                cm_name = self.get_full_cm_name(item_name, category, freq)
                loader = BaseAlpha.get_cm(cm_name)

                # Check if loader has special usage method
                if hasattr(loader, "quarters_usage"):
                    print(f"\n📊 Special features available for '{item_name}':\n")
                    loader.quarters_usage()
                else:
                    print(get_standard_item_usage(item_name))
            except ValueError as e:
                print(f"Error: {e}")
                print(f"\nTry searching: cf.search('{item_name}')")

    def _get_default_search_items(self):
        """Get default search items with universe-specific filtering."""
        if self.universe_name == "us_stock":
            # US: exclude non-PIT Financial (only PIT Financial Statements is useful)
            exclude = set()
            for key, items in self.cm_dict.items():
                _, cat, subcat = key
                if cat == "Financial" and not subcat.startswith("PIT"):
                    exclude.update(items)
            return sorted(set(self.item_list) - exclude)
        return self.item_list

    def _calc_fuzzy_score(self, query: str, text: str) -> float:
        """Calculate fuzzy match score between query and text."""
        import re
        from difflib import SequenceMatcher

        scores = []

        # Basic sequence matching
        sim = SequenceMatcher(None, query, text).ratio()
        if sim > 0.4:
            scores.append(sim * 0.6)

        # Clean pattern matching (remove separators)
        clean_q = re.sub(r"[\s_\.-]", "", query)
        clean_t = re.sub(r"[\s_\.-]", "", text)
        if clean_q != query or clean_t != text:
            clean_sim = SequenceMatcher(None, clean_q, clean_t).ratio()
            if clean_sim > 0.5:
                scores.append(clean_sim * 0.55)

        # Word-level matching
        q_words = set(re.split(r"[\s_\.-]+", query))
        t_words = set(re.split(r"[\s_\.-]+", text))
        if q_words and t_words:
            overlap = len(q_words & t_words) / len(q_words)
            if overlap > 0:
                scores.append(overlap * 0.5)

        return max(scores) if scores else 0

    def search(
        self,
        query,
        category=None,
        subcategory=None,
        exclude_subcategory=None,
        max_results=10,
    ):
        """
        Search items by name and description with fuzzy matching.

        Args:
            query (str): Search query
            category (str, optional): Filter by category
            subcategory (str, optional): Filter by subcategory ("pit-*" for prefix match)
            exclude_subcategory (str, optional): Exclude subcategories ("pit-*" for prefix)
            max_results (int): Maximum number of results to return

        Returns:
            pd.DataFrame: DataFrame with 'description' and 'note' columns
        """
        import pandas as pd

        if not query:
            return pd.DataFrame(columns=["description", "note"])

        # Get search items
        if category or subcategory or exclude_subcategory:
            search_items = self.get_items_by_category(
                category, subcategory, exclude_subcategory
            )
        else:
            search_items = self._get_default_search_items()

        query_lower = query.lower()
        metadata = self._load_metadata(self.universe_name)
        results = []

        for item in search_items:
            item_lower = item.lower()

            # Score by match type
            if item_lower == query_lower:
                score = 1.0
            elif item_lower.startswith(query_lower):
                score = 0.9
            elif query_lower in item_lower:
                score = 0.7
            else:
                score = self._calc_fuzzy_score(query_lower, item_lower)

            # Check description if name match is weak
            if score < 0.5:
                value = metadata.get(item, "")
                desc = (
                    value.get("description", "") if isinstance(value, dict) else value
                )
                if desc:
                    desc_lower = desc.lower()
                    if query_lower in desc_lower:
                        score = max(score, 0.5)
                    else:
                        score = max(
                            score, self._calc_fuzzy_score(query_lower, desc_lower) * 0.7
                        )

            if score > 0.3:
                results.append((item, score))

        # Sort by score and build result
        results.sort(key=lambda x: x[1], reverse=True)
        top_items = [r[0] for r in results[:max_results]]

        return pd.DataFrame(
            [
                {"description": d, "note": n}
                for d, n in (self.get_description(i) for i in top_items)
            ],
            index=top_items,
        )

    def summary(self):
        """Show a compact summary of available categories and item counts."""
        category_counts = {}
        for key, item_list in self.cm_dict.items():
            _, category, subcategory = key
            if category not in category_counts:
                category_counts[category] = {"subcategories": 0, "total_items": 0}
            category_counts[category]["subcategories"] += 1
            category_counts[category]["total_items"] += len(item_list)

        print("Content Model Summary:")
        print("-" * 40)
        for category, info in sorted(category_counts.items()):
            print(
                f"{category}: {info['subcategories']} subcategories, {info['total_items']} items"
            )

    def info(self, category=None):
        """Show detailed info for a specific category or all categories."""
        if category:
            matching_keys = [key for key in self.cm_dict.keys() if key[1] == category]
            if not matching_keys:
                print(
                    f"Category '{category}' not found. Available: {', '.join(self.categories)}"
                )
                return

            print(f"{category} Details:")
            print("-" * 40)
            for key in matching_keys:
                _, cat, subcat = key
                item_count = len(self.cm_dict[key])
                sample_items = ", ".join(sorted(self.cm_dict[key])[:5])
                print(f"  {subcat} ({item_count} items): {sample_items}...")
        else:
            self.summary()

    @classmethod
    def reset_cache(cls):
        """Resets the global cache."""
        cls._global_cache = None

    @classmethod
    def initialize_cache(cls, maxsize, ttl):
        """Initializes the global cache with given parameters."""
        cls._global_cache = TTLCache(maxsize=maxsize, ttl=ttl)
