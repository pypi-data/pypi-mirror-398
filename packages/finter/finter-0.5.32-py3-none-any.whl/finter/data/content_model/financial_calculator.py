"""
Financial Calculator with fluent interface.

Provides a fluent API for financial data transformations:
1. Wide format → Long format (polars)
2. Apply rolling calculations or expressions
3. Long format → Wide format with forward fill

Usage:
    # Rolling calculation
    result = FC(df_assets).apply_rolling(quarters=4, operation='sum').to_wide(forward_fill=True)

    # Expression calculation
    result = FC.join({
        'assets': FC(df_assets),
        'current': FC(df_current)
    }).apply_expression("assets - current").to_wide()
"""

from typing import Dict, Literal

import pandas as pd
import polars as pl


class FinancialCalculator:
    """
    Financial data calculator with fluent interface.

    Usage:
        # Rolling calculation
        result = FC(df_assets).apply_rolling(quarters=4, operation='sum').to_wide(forward_fill=True)

        # Expression calculation
        result = FC.join({
            'assets': FC(df_assets),
            'current': FC(df_current)
        }).apply_expression("assets - current").to_wide()
    """

    def __init__(self, df: pd.DataFrame | pl.DataFrame, trading_days=None, id_table=None):
        """
        Initialize with DataFrame (wide pandas or long polars format).

        Args:
            df: Wide format pandas DataFrame or long format polars DataFrame
                - Wide: (pit as index, ids as columns, dict/numeric values)
                - Long: columns [pit, id, fiscal, value] or [pit, id, value]
            trading_days: Optional trading days index for to_wide() reindexing
                         If provided, to_wide() will automatically reindex to these days
            id_table: Optional id_table for gvkey -> gvkeyiid mapping (us_stock)
                     If provided, to_wide() will convert to security-level by default
        """
        if isinstance(df, pd.DataFrame):
            # Wide format -> convert to long
            self._df_long = self._to_long_impl(df)
        elif isinstance(df, pl.DataFrame):
            # Already long format
            self._df_long = df
        else:
            raise TypeError(f"Expected pd.DataFrame or pl.DataFrame, got {type(df)}")

        self._trading_days = trading_days
        self._id_table = id_table

    @property
    def df_long(self) -> pl.DataFrame:
        """Get the underlying long format DataFrame."""
        return self._df_long

    def __repr__(self) -> str:
        """Return string representation showing the underlying DataFrame."""
        return repr(self._df_long)

    def __getattr__(self, name: str):
        """
        Delegate unknown attributes to the underlying polars DataFrame.

        This allows using polars methods directly on FC instances:
            fc.join({...}).filter(pl.col("id") == 12170).sort("pit").to_wide()

        Automatically wraps DataFrame results back into FinancialCalculator
        to support method chaining with both polars and FC methods.
        """
        attr = getattr(self._df_long, name)

        # If it's a callable (method), wrap it to handle DataFrame results
        if callable(attr):

            def wrapped_method(*args, **kwargs):
                result = attr(*args, **kwargs)
                # If result is a DataFrame, wrap it back into FinancialCalculator
                if isinstance(result, pl.DataFrame):
                    return FinancialCalculator(result, trading_days=self._trading_days, id_table=self._id_table)
                return result

            return wrapped_method

        # If it's not a callable (e.g., attribute), return as-is
        return attr

    def apply_rolling(
        self,
        quarters: int = 4,
        operation: Literal["mean", "sum", "diff", "last"] = "mean",
        variables: list[str] | None = None,
    ) -> "FinancialCalculator":
        """
        Apply rolling quarters calculation.

        Args:
            quarters: Number of quarters (default: 4)
            operation: Aggregation operation
                - 'mean': n quarters average
                - 'sum': n quarters sum
                - 'diff': current - n quarters ago
                - 'last': n quarters ago value (quarters=0 for current)
            variables: Optional list of variable names to apply rolling to.
                      If None, applies to the 'value' column (default behavior).
                      If specified, only those variables are rolled, others are kept as-is.

        Returns:
            New FinancialCalculator instance with rolling calculation applied

        Example:
            # Apply rolling to specific variables after join
            joined = FC.join({"assets": fc1, "current": fc2})
            result = joined.apply_rolling(4, 'sum', variables=['assets'])
            # assets will be rolled, current will be preserved
        """
        # Get all column names except [id, pit, fiscal]
        var_cols = [
            col for col in self._df_long.columns if col not in ["id", "pit", "fiscal"]
        ]

        # If no variables specified and we have a 'value' column, use default behavior
        if variables is None:
            if "value" in var_cols:
                result_long = self._apply_rolling_impl(
                    self._df_long, quarters, operation
                )
                return FinancialCalculator(result_long, trading_days=self._trading_days, id_table=self._id_table)
            else:
                # No value column and no variables specified - error
                raise ValueError(
                    f"No 'value' column found and no variables specified. "
                    f"Available columns: {var_cols}. "
                    f"Use variables parameter to specify which columns to roll."
                )

        # Apply rolling to specified variables only
        result_dfs = {}
        for var in var_cols:
            if var in variables:
                # Apply rolling to this variable
                df_var = self._df_long.select(["id", "pit", "fiscal", var]).rename(
                    {var: "value"}
                )
                rolled = self._apply_rolling_impl(df_var, quarters, operation)
                result_dfs[var] = rolled
            else:
                # Keep as-is
                df_var = self._df_long.select(["id", "pit", "fiscal", var]).rename(
                    {var: "value"}
                )
                result_dfs[var] = df_var

        # Join all results back
        result_long = self._join_long_dfs_impl(result_dfs, join_type="outer")
        return FinancialCalculator(result_long, trading_days=self._trading_days, id_table=self._id_table)

    def apply_expression(self, expression: str) -> "FinancialCalculator":
        """
        Apply expression calculation on long format data.

        Args:
            expression: Expression to evaluate (e.g., "var_revenue - var_cogs")

        Returns:
            New FinancialCalculator instance with expression applied
        """
        result_long = self._apply_expression_impl(self._df_long, expression)
        return FinancialCalculator(result_long, trading_days=self._trading_days, id_table=self._id_table)

    def to_wide(
        self,
        forward_fill: bool = True,
        forward_fill_limit: int = 500,
        trading_days=None,
        security: bool = True,
    ) -> pd.DataFrame:
        """
        Convert to wide format.

        Args:
            forward_fill: Whether to apply forward fill (default: True)
            forward_fill_limit: Maximum number of rows to forward fill (default: 500)
            trading_days: Optional trading days for reindexing.
                         If None, uses trading_days from initialization (via cf.get_fc).
                         Set to False to disable reindexing.
            security: Whether to convert to security-level (gvkeyiid) columns (default: True)
                     Only applies if id_table is available (us_stock)

        Returns:
            Wide format pandas DataFrame (pit as index, ids as columns, numeric values)
        """
        # Use instance trading_days if not explicitly provided
        if trading_days is None:
            trading_days = self._trading_days

        # Convert to wide
        result = self._to_wide_impl(self._df_long)

        # Convert to security-level if id_table available and security=True
        if security and self._id_table is not None:
            result = self._to_security_impl(result, self._id_table)

        # Reindex to trading days if available
        if trading_days is not None and trading_days is not False:
            # First reindex to all dates (including weekends/holidays)
            result = result.reindex(
                pd.date_range(start=min(trading_days), end=max(trading_days))
            )
            # Forward fill to propagate values across all dates
            if forward_fill:
                result = result.ffill(limit=forward_fill_limit)
            # Finally reindex to trading_days only
            result = result.reindex(trading_days)

        return result

    @staticmethod
    def _to_security_impl(df: pd.DataFrame, id_table: pd.DataFrame) -> pd.DataFrame:
        """
        Convert company-level (gvkey) columns to security-level (gvkeyiid) columns.

        Args:
            df: DataFrame with gvkey columns (6-digit, int or str)
            id_table: DataFrame with gvkey, iid, gvkeyiid columns

        Returns:
            DataFrame with gvkeyiid columns (8-9 digit str)
        """
        # Normalize column names to str with zero-padding (gvkey format)
        df_cols = {str(col).zfill(6): col for col in df.columns}

        # Broadcast gvkey -> gvkeyiid
        result = {}
        for gvkey, gvkeyiid in zip(id_table["gvkey"], id_table["gvkeyiid"]):
            if gvkey in df_cols:
                result[gvkeyiid] = df[df_cols[gvkey]]

        return pd.DataFrame(result, index=df.index)

    @classmethod
    def join(
        cls,
        dfs: Dict[str, "FinancialCalculator"],
        join_type: Literal["inner", "outer"] = "outer",
    ) -> "FinancialCalculator":
        """
        Join multiple FinancialCalculator instances on [id, pit, fiscal].

        Args:
            dfs: Dict mapping variable names to FinancialCalculator instances
            join_type: 'inner' or 'outer' join (default: 'outer')

        Returns:
            New FinancialCalculator instance with joined data

        Example:
            result = FC.join({
                'assets': FC(df_assets),
                'current': FC(df_current)
            }).apply_expression("assets - current").to_wide()
        """
        long_dfs = {name: fc._df_long for name, fc in dfs.items()}
        result_long = cls._join_long_dfs_impl(long_dfs, join_type)

        # Use trading_days and id_table from first FC that has it
        trading_days = None
        id_table = None
        for fc in dfs.values():
            if fc._trading_days is not None and trading_days is None:
                trading_days = fc._trading_days
            if fc._id_table is not None and id_table is None:
                id_table = fc._id_table

        return FinancialCalculator(result_long, trading_days=trading_days, id_table=id_table)

    @staticmethod
    def _to_long_impl(df: pd.DataFrame) -> pl.DataFrame:
        """
        Convert wide format DataFrame to long format (internal implementation).

        Args:
            df: Wide format DataFrame (pit as index, ids as columns, dict/numeric values)

        Returns:
            Long format polars DataFrame with columns: [pit, id, fiscal, value]
        """
        rows = []
        for idx, value in df.stack().items():
            if isinstance(value, dict):
                # Raw data with fiscal: {fiscal: amount}
                for fiscal, amount in value.items():
                    # if pd.notna(amount):
                    rows.append((*idx, fiscal, amount))
            elif pd.notna(value):
                # Simple numeric value (from quarters calculation)
                rows.append((*idx, None, value))

        if not rows:
            # Empty DataFrame with correct schema
            df_long = pd.DataFrame(rows, columns=["pit", "id", "fiscal", "value"])
            df_long_pl = pl.from_pandas(df_long)

            return df_long_pl.filter(pl.col("fiscal").is_not_null()).unique(
                subset=["id", "pit", "fiscal"], keep="last"
            )

        # Create DataFrame
        df_long = pl.DataFrame(
            {
                "pit": [r[0] for r in rows],
                "id": [r[1] for r in rows],
                "fiscal": [r[2] for r in rows],
                "value": [r[3] for r in rows],
            }
        )

        # Ensure correct types
        # Note: id can be int (kr_stock, us_stock) or str (id_stock)
        id_dtype = df_long.schema["id"]
        if id_dtype in (pl.Utf8, pl.String):
            # String id (e.g., id_stock: "AADI", "AALI")
            df_long = df_long.with_columns(
                [
                    pl.col("pit").cast(pl.Date),
                    pl.col("id").cast(pl.Utf8),
                    pl.col("fiscal").cast(pl.Int64),
                    pl.col("value").cast(pl.Float64),
                ]
            )
        else:
            # Numeric id (e.g., kr_stock, us_stock)
            df_long = df_long.with_columns(
                [
                    pl.col("pit").cast(pl.Date),
                    pl.col("id").cast(pl.Int64),
                    pl.col("fiscal").cast(pl.Int64),
                    pl.col("value").cast(pl.Float64),
                ]
            )

        return df_long

    @staticmethod
    def _apply_rolling_impl(
        df_long: pl.DataFrame,
        quarters: int = 4,
        operation: Literal["mean", "sum", "diff", "last"] = "mean",
    ) -> pl.DataFrame:
        """
        Apply rolling quarters calculation (internal implementation).

        Args:
            df_long: Long format DataFrame with columns: [pit, id, fiscal, value]
            quarters: Number of quarters (default: 4)
            operation: Aggregation operation

        Returns:
            Long format DataFrame with columns: [pit, id, fiscal, value]
            (fiscal = cummax_fiscal, the reference fiscal period for rolling calculation)
        """
        # Calculate cummax_fiscal: maximum fiscal WHERE value is not null
        # This ensures we only use fiscals with actual values
        df_base = df_long.sort(["id", "pit", "fiscal"]).with_columns(
            [
                pl.when(pl.col("value").is_not_null())
                .then(pl.col("fiscal"))
                .otherwise(None)
                .cum_max()
                .over("id")
                .alias("cummax_fiscal")
            ]
        )

        # For each (id, pit), keep only the row where fiscal == cummax_fiscal AND value is not null
        # This ensures each (id, pit) has only one row with the maximum fiscal that has a value
        df_base_filtered = df_base.filter(
            (pl.col("fiscal") == pl.col("cummax_fiscal"))
            & (pl.col("value").is_not_null())
        ).unique(subset=["id", "pit"], keep="last")

        # Calculate each quarter
        q_dfs = []
        # Determine how many quarters to calculate
        if operation == "last" and quarters == 0:
            n_quarters_to_calc = 1  # Only need q0 for current quarter
        elif operation in ["last", "diff"]:
            n_quarters_to_calc = quarters + 1  # Need q0 ~ q{quarters}
        else:  # mean, sum
            n_quarters_to_calc = quarters  # Need q0 ~ q{quarters-1}

        for i in range(n_quarters_to_calc):
            # Target fiscal = cummax_fiscal - i quarters
            df_temp = df_base_filtered.select(
                ["id", "pit", "cummax_fiscal"]
            ).with_columns(
                [
                    FinancialCalculator._subtract_quarters(
                        pl.col("cummax_fiscal"), i
                    ).alias("target_fiscal")
                ]
            )

            # Self-join on [id, fiscal] to find the target fiscal
            # Join to ALL fiscals in original df_base (not filtered)
            df_joined = df_temp.join(
                df_base.select(["id", "pit", "fiscal", "value"]),
                left_on=["id", "target_fiscal"],
                right_on=["id", "fiscal"],
                how="left",
                suffix="_right",
            )

            # Filter: pit_right <= pit (only use published data)
            # Group by [id, pit] and take max value
            df_q = (
                df_joined.filter(
                    (pl.col("pit_right") <= pl.col("pit"))
                    | pl.col("pit_right").is_null()
                )
                .group_by(["id", "pit"])
                .agg([pl.col("value").max().alias(f"q{i}")])
            )

            q_dfs.append(df_q)

        # Join all quarters to base (filtered)
        df_result = df_base_filtered
        for df_q in q_dfs:
            df_result = df_result.join(df_q, on=["id", "pit"], how="left")

        # Calculate aggregation only when all required quarters are available
        if operation == "mean":
            # Check if all quarters are non-null
            all_quarters_valid = pl.col("q0").is_not_null()
            for i in range(1, quarters):
                all_quarters_valid = all_quarters_valid & pl.col(f"q{i}").is_not_null()

            # Calculate sum
            sum_expr = pl.col("q0")
            for i in range(1, quarters):
                sum_expr = sum_expr + pl.col(f"q{i}")

            # Return value only if all quarters are available
            result_expr = (
                pl.when(all_quarters_valid)
                .then(sum_expr / quarters)
                .otherwise(None)
                .alias("value")
            )

        elif operation == "sum":
            # Check if all quarters are non-null
            all_quarters_valid = pl.col("q0").is_not_null()
            for i in range(1, quarters):
                all_quarters_valid = all_quarters_valid & pl.col(f"q{i}").is_not_null()

            # Calculate sum
            sum_expr = pl.col("q0")
            for i in range(1, quarters):
                sum_expr = sum_expr + pl.col(f"q{i}")

            # Return value only if all quarters are available
            result_expr = (
                pl.when(all_quarters_valid)
                .then(sum_expr)
                .otherwise(None)
                .alias("value")
            )

        elif operation == "diff":
            # Check if both q0 and q{quarters} are non-null
            both_valid = (
                pl.col("q0").is_not_null() & pl.col(f"q{quarters}").is_not_null()
            )
            result_expr = (
                pl.when(both_valid)
                .then(pl.col("q0") - pl.col(f"q{quarters}"))
                .otherwise(None)
                .alias("value")
            )

        elif operation == "last":
            if quarters == 0:
                # Check if q0 is non-null
                result_expr = (
                    pl.when(pl.col("q0").is_not_null())
                    .then(pl.col("q0"))
                    .otherwise(None)
                    .alias("value")
                )
            else:
                # Check if q{quarters} is non-null
                result_expr = (
                    pl.when(pl.col(f"q{quarters}").is_not_null())
                    .then(pl.col(f"q{quarters}"))
                    .otherwise(None)
                    .alias("value")
                )

        else:
            raise ValueError(
                f"operation must be one of ['mean', 'sum', 'diff', 'last'], got '{operation}'"
            )

        # Calculate the result
        df_result = df_result.with_columns([result_expr])

        # Return result with columns: [pit, id, fiscal, value]
        # Already filtered to cummax_fiscal only, so no need to filter again
        return df_result.select(["pit", "id", "fiscal", "value"]).sort(
            ["id", "pit", "fiscal"]
        )

    @staticmethod
    def _join_long_dfs_impl(
        dfs: Dict[str, pl.DataFrame],
        join_type: Literal["inner", "outer"] = "outer",
    ) -> pl.DataFrame:
        """
        Join multiple long format DataFrames.

        For each (id, pit, fiscal) combination, finds the latest value published
        at or before that pit for each variable.

        Args:
            dfs: Dict mapping variable names to their long format DataFrames
            join_type: 'inner' or 'outer' join (default: 'outer')

        Returns:
            Joined DataFrame with columns: [id, pit, fiscal, name1, name2, ...]
        """
        if not dfs:
            raise ValueError("No DataFrames to join")

        # Step 1: Collect all unique (id, pit, fiscal) combinations
        all_combinations = None
        for df_long in dfs.values():
            df_keys = (
                df_long.filter(pl.col("fiscal").is_not_null())
                .select(["id", "pit", "fiscal"])
                .unique()
            )
            if all_combinations is None:
                all_combinations = df_keys
            else:
                if join_type == "outer":
                    # Union all combinations
                    all_combinations = pl.concat([all_combinations, df_keys]).unique()
                else:  # inner
                    # Intersection only
                    all_combinations = all_combinations.join(
                        df_keys, on=["id", "pit", "fiscal"], how="inner"
                    )

        assert all_combinations is not None

        # Step 2: For each variable, find the latest value <= pit for each (id, fiscal)
        result = all_combinations
        for name, df_long in dfs.items():
            df_clean = df_long.filter(pl.col("fiscal").is_not_null()).unique(
                subset=["id", "pit", "fiscal"], keep="last"
            )

            # For each (id, pit, fiscal) in result, find the latest value from df_clean
            # where (id, fiscal) matches and pit_right <= pit_left
            var_result = (
                all_combinations.join(
                    df_clean.select(["id", "pit", "fiscal", "value"]),
                    on=["id", "fiscal"],
                    how="left",
                    suffix="_right",
                )
                # Filter: only keep rows where pit_right <= pit_left
                .filter(
                    (pl.col("pit_right") <= pl.col("pit"))
                    | pl.col("pit_right").is_null()
                )
                # Group by (id, pit, fiscal) and take the row with max pit_right
                .group_by(["id", "pit", "fiscal"], maintain_order=True)
                .agg(
                    [
                        pl.col("value")
                        .sort_by("pit_right", descending=True)
                        .first()
                        .alias(name)
                    ]
                )
            )

            # Join this variable's result to the main result
            result = result.join(var_result, on=["id", "pit", "fiscal"], how="left")

        return result.sort(["id", "pit", "fiscal"])

    @staticmethod
    def _apply_expression_impl(df_long: pl.DataFrame, expression: str) -> pl.DataFrame:
        """
        Apply expression calculation (internal implementation).

        Args:
            df_long: Long format DataFrame with variable columns
            expression: Expression to evaluate (e.g., "assets - current")

        Returns:
            Long format DataFrame with columns: [id, pit, fiscal, value]
        """
        # Get all variable columns (exclude id, pit, fiscal)
        var_cols = [
            col for col in df_long.columns if col not in ["id", "pit", "fiscal"]
        ]

        if not var_cols:
            raise ValueError("No variable columns found in DataFrame")

        # Replace variable names with pl.col("var_name") for evaluation
        # Use word boundaries to avoid partial replacements (e.g., "sales" in "sales_shift_1")
        import re
        pl_expr = expression
        for var_col in sorted(var_cols, key=len, reverse=True):
            pl_expr = re.sub(rf'\b{re.escape(var_col)}\b', f'pl.col("{var_col}")', pl_expr)

        try:
            # Evaluate expression safely
            result_expr = eval(pl_expr, {"pl": pl, "__builtins__": {}}, {})

            df_result = df_long.with_columns(result_expr.alias("value"))

            # Keep only necessary columns
            return df_result.select(["id", "pit", "fiscal", "value"])

        except Exception as e:
            raise ValueError(f"Failed to evaluate expression '{expression}': {e}")

    @staticmethod
    def _to_wide_impl(df_long: pl.DataFrame) -> pd.DataFrame:
        """
        Convert long format to wide format (internal implementation).

        If df_long has fiscal column with multiple fiscals per (id, pit),
        automatically selects max fiscal with non-null value per (id, pit).

        Args:
            df_long: Long format DataFrame with columns: [pit, id, value]
                     or [pit, id, fiscal, value]
                     or [pit, id, fiscal, var1, var2, ...] (multiple variables)

        Returns:
            Wide format pandas DataFrame (pit as index, ids as columns, numeric values)
            For multiple variables, returns MultiIndex columns (variable, id)
        """
        # Get variable columns (exclude id, pit, fiscal)
        var_cols = [
            col for col in df_long.columns if col not in ["id", "pit", "fiscal"]
        ]

        # Single value column (standard case)
        if "value" in var_cols and len(var_cols) == 1:
            # If fiscal exists, select max fiscal with non-null value per (id, pit)
            if "fiscal" in df_long.columns:
                df_long = FinancialCalculator._apply_rolling_impl(
                    df_long, quarters=0, operation="last"
                )

            # Simple pivot (numeric values)
            df_wide = df_long.pivot(index="pit", on="id", values="value").sort("pit")

            # Convert to pandas
            df_wide_pd = df_wide.to_pandas().set_index("pit").sort_index()

            # Convert index to datetime if possible
            try:
                df_wide_pd.index = pd.to_datetime(df_wide_pd.index)
            except Exception:
                pass

            # Convert column names to int if possible
            try:
                df_wide_pd.columns = df_wide_pd.columns.astype(int)
            except (ValueError, TypeError):
                pass

            return df_wide_pd

        # Multiple variables - create separate DataFrames and concat
        wide_dfs = []
        for var in var_cols:
            # Create temporary df with this variable as 'value'
            df_var = df_long.select(
                ["id", "pit", "fiscal", var]
                if "fiscal" in df_long.columns
                else ["id", "pit", var]
            )
            df_var = df_var.rename({var: "value"})

            # Apply rolling if fiscal exists
            if "fiscal" in df_var.columns:
                df_var = FinancialCalculator._apply_rolling_impl(
                    df_var, quarters=0, operation="last"
                )

            # Pivot
            df_wide = df_var.pivot(index="pit", on="id", values="value").sort("pit")
            df_wide_pd = df_wide.to_pandas().set_index("pit").sort_index()

            # Add variable name to column MultiIndex
            df_wide_pd.columns = pd.MultiIndex.from_product([[var], df_wide_pd.columns])
            wide_dfs.append(df_wide_pd)

        # Concatenate all variables
        result = pd.concat(wide_dfs, axis=1)

        # Convert index to datetime if possible
        try:
            result.index = pd.to_datetime(result.index)
        except Exception:
            pass

        return result

    @staticmethod
    def _subtract_quarters(fiscal_col, n: int):
        """
        Subtract n quarters from fiscal period.

        Args:
            fiscal_col: YYYYQQ format fiscal column
            n: Number of quarters to subtract

        Returns:
            New fiscal period (YYYYQQ format)
        """
        year = fiscal_col // 100
        quarter = fiscal_col % 100
        total_quarters = year * 4 + quarter - n
        new_year = (total_quarters - 1) // 4
        new_quarter = ((total_quarters - 1) % 4) + 1
        return new_year * 100 + new_quarter
