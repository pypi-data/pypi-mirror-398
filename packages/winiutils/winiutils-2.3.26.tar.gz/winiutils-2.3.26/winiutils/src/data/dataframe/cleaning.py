"""DataFrame cleaning pipeline utilities using Polars.

This module provides an abstract base class for building extensible DataFrame
cleaning pipelines. The ``CleaningDF`` class implements an 8-step cleaning
pipeline that can be customized by implementing abstract methods in child classes.

The cleaning pipeline executes the following operations in order:
    1. Rename columns to standardized names
    2. Drop columns not in the schema
    3. Fill null values with specified defaults
    4. Convert columns to correct data types
    5. Drop rows where specified column subsets are entirely null
    6. Handle duplicates by aggregating and removing
    7. Sort the DataFrame by specified columns
    8. Validate data quality (types, nulls, NaN values)

Example:
    >>> import polars as pl
    >>> from winiutils.src.data.dataframe.cleaning import CleaningDF
    >>>
    >>> class UserCleaner(CleaningDF):
    ...     USER_ID = "user_id"
    ...     EMAIL = "email"
    ...
    ...     @classmethod
    ...     def get_rename_map(cls):
    ...         return {cls.USER_ID: "UserId", cls.EMAIL: "Email"}
    ...
    ...     # ... implement other abstract methods
"""

from abc import abstractmethod
from collections.abc import Callable
from typing import Any

import polars as pl
from polars.datatypes.classes import FloatType

from winiutils.src.data.structures.dicts import reverse_dict
from winiutils.src.oop.mixins.mixin import ABCLoggingMixin


class CleaningDF(ABCLoggingMixin):
    """Abstract base class for cleaning and standardizing DataFrames using Polars.

    This class provides a comprehensive pipeline for importing, cleaning, and
    standardizing data from various sources before loading into databases or
    other systems. It enforces data quality standards through a series of
    configurable cleaning operations.

    The cleaning pipeline executes in the following order:
        1. Rename columns according to a standardized naming scheme
        2. Drop columns not in the schema
        3. Fill null values with specified defaults
        4. Convert columns to correct data types and apply custom transformations
        5. Drop rows where specified column subsets are entirely null
        6. Handle duplicates by aggregating values and removing duplicates
        7. Sort the DataFrame by specified columns
        8. Validate data quality (correct dtypes, no nulls in required columns,
           no NaN values)

    Child classes must implement abstract methods to define the cleaning
    configuration:
        - ``get_rename_map()``: Define column name mappings
        - ``get_col_dtype_map()``: Define expected data types for each column
        - ``get_drop_null_subsets()``: Define which column subsets trigger row
          deletion
        - ``get_fill_null_map()``: Define null value fill strategies
        - ``get_sort_cols()``: Define sort order
        - ``get_unique_subsets()``: Define duplicate detection criteria
        - ``get_no_null_cols()``: Define columns that cannot contain nulls
        - ``get_col_converter_map()``: Define custom column transformations
        - ``get_add_on_duplicate_cols()``: Define columns to aggregate when
          duplicates are found
        - ``get_col_precision_map()``: Define rounding precision for float columns

    Attributes:
        df: The cleaned Polars DataFrame after the pipeline has executed.

    Note:
        - Define column names as class-level string constants for reusability
        - NaN values are automatically converted to null for consistency
        - The class inherits automatic method logging from ``ABCLoggingMixin``

    Example:
        >>> class UserCleaner(CleaningDF):
        ...     USER_ID = "user_id"
        ...     EMAIL = "email"
        ...     SCORE = "score"
        ...
        ...     @classmethod
        ...     def get_col_dtype_map(cls):
        ...         return {cls.USER_ID: pl.Int64, cls.EMAIL: pl.Utf8}
    """

    @classmethod
    @abstractmethod
    def get_rename_map(cls) -> dict[str, str]:
        """Define column name mappings for standardization.

        This abstract method must be implemented in child classes to specify how
        raw input column names should be renamed to standardized names. Renaming
        is the first operation in the cleaning pipeline, executed before all other
        cleaning operations.

        The mapping format follows the CleaningDF convention of mapping
        standardized names to raw input names. The reverse mapping is applied
        to the DataFrame during cleaning.

        Returns:
            Dictionary mapping standardized column names (keys) to raw input
            column names (values).

        Example:
            >>> @classmethod
            ... def get_rename_map(cls):
            ...     return {
            ...         "user_id": "UserId",
            ...         "email": "Email_Address",
            ...         "created_at": "CreatedDate",
            ...     }
        """

    @classmethod
    @abstractmethod
    def get_col_dtype_map(cls) -> dict[str, type[pl.DataType]]:
        """Define the expected data type for each column in the cleaned DataFrame.

        This abstract method must be implemented in child classes to specify the
        target data types for all columns. The DataFrame will be validated against
        this schema after cleaning, and a TypeError will be raised if any column
        has an incorrect type.

        Returns:
            Dictionary mapping standardized column names to their expected
            Polars data types.

        Example:
            >>> @classmethod
            ... def get_col_dtype_map(cls):
            ...     return {
            ...         "user_id": pl.Int64,
            ...         "email": pl.Utf8,
            ...         "created_at": pl.Date,
            ...         "score": pl.Float64,
            ...     }
        """

    @classmethod
    @abstractmethod
    def get_drop_null_subsets(cls) -> tuple[tuple[str, ...], ...]:
        """Define column subsets for dropping rows with all-null values.

        This abstract method specifies which column subsets should trigger row
        deletion. A row is dropped if ALL columns in a subset are null. Multiple
        subsets can be defined to apply different null-dropping rules. If no
        subsets are defined, rows where all columns are null will be dropped.

        Returns:
            Tuple of column name tuples, where each inner tuple represents one
            subset. A row is dropped if all columns in any subset are null.

        Example:
            >>> @classmethod
            ... def get_drop_null_subsets(cls):
            ...     return (
            ...         ("email", "phone"),  # Drop if both are null
            ...         ("address_line1",),  # Drop if null
            ...     )
        """

    @classmethod
    @abstractmethod
    def get_fill_null_map(cls) -> dict[str, Any]:
        """Define null value fill strategies for each column.

        This abstract method specifies default values to fill null entries in
        each column. This is applied early in the cleaning pipeline after
        column renaming.

        Returns:
            Dictionary mapping column names to their fill values. The fill
            value can be any type appropriate for the column's data type.

        Example:
            >>> @classmethod
            ... def get_fill_null_map(cls):
            ...     return {
            ...         "email": "",
            ...         "phone": "",
            ...         "score": 0,
            ...         "status": "unknown",
            ...     }
        """

    @classmethod
    @abstractmethod
    def get_sort_cols(cls) -> tuple[tuple[str, bool], ...]:
        """Define the sort order for the cleaned DataFrame.

        This abstract method specifies which columns to sort by and in what
        order (ascending or descending). Sorting is applied near the end of
        the cleaning pipeline, after all data transformations are complete.

        Returns:
            Tuple of (column_name, is_descending) tuples. Each tuple specifies
            a column and sort direction. Columns are sorted in the order they
            appear. True = descending, False = ascending.

        Example:
            >>> @classmethod
            ... def get_sort_cols(cls):
            ...     return (
            ...         ("created_at", True),   # Descending
            ...         ("user_id", False),     # Ascending
            ...     )
        """

    @classmethod
    @abstractmethod
    def get_unique_subsets(cls) -> tuple[tuple[str, ...], ...]:
        """Define column subsets for duplicate detection and removal.

        This abstract method specifies which column combinations define
        uniqueness. Rows are considered duplicates if they have identical
        values in all columns of a subset. When duplicates are found, values
        in columns specified by ``get_add_on_duplicate_cols()`` are summed,
        and the first row is kept.

        Returns:
            Tuple of column name tuples, where each inner tuple represents
            one uniqueness constraint. Duplicates are detected and handled
            for each subset independently.

        Example:
            >>> @classmethod
            ... def get_unique_subsets(cls):
            ...     return (
            ...         ("user_id", "date"),      # Unique by user_id and date
            ...         ("transaction_id",),      # Unique by transaction_id
            ...     )
        """

    @classmethod
    @abstractmethod
    def get_no_null_cols(cls) -> tuple[str, ...]:
        """Define columns that must not contain null values.

        This abstract method specifies which columns are required to have
        non-null values. A ValueError is raised during the final validation
        step if any of these columns contain null values.

        Returns:
            Tuple of column names that must not contain null values.

        Example:
            >>> @classmethod
            ... def get_no_null_cols(cls):
            ...     return ("user_id", "email", "created_at")
        """

    @classmethod
    @abstractmethod
    def get_col_converter_map(
        cls,
    ) -> dict[str, Callable[[pl.Series], pl.Series]]:
        """Define custom conversion functions for columns.

        This abstract method specifies custom transformations to apply to
        columns after standard conversions (string stripping, float rounding).
        Each function receives a Polars Series and returns a transformed
        Series. Use ``skip_col_converter`` as a placeholder for columns that
        don't need custom conversion.

        Returns:
            Dictionary mapping column names to their conversion functions.
            Each function takes a Series and returns a transformed Series.

        Example:
            >>> @classmethod
            ... def get_col_converter_map(cls):
            ...     return {
            ...         "email": lambda s: s.str.to_lowercase(),
            ...         "phone": cls.parse_phone_number,
            ...         "created_at": cls.skip_col_converter,
            ...     }
        """

    @classmethod
    @abstractmethod
    def get_add_on_duplicate_cols(cls) -> tuple[str, ...]:
        """Define columns to aggregate when duplicate rows are found.

        This abstract method specifies which columns should have their values
        summed when duplicate rows are detected (based on
        ``get_unique_subsets()``). The summed values are kept in the first row,
        and duplicate rows are removed.

        Returns:
            Tuple of column names whose values should be summed when duplicates
            are found.

        Example:
            >>> @classmethod
            ... def get_add_on_duplicate_cols(cls):
            ...     return ("quantity", "revenue", "impressions")
        """

    @classmethod
    @abstractmethod
    def get_col_precision_map(cls) -> dict[str, int]:
        """Define rounding precision for float columns.

        This abstract method specifies the number of decimal places to round
        float columns to. Rounding is applied during the standard conversion
        phase and uses Kahan summation to compensate for floating-point
        rounding errors.

        Returns:
            Dictionary mapping float column names to their precision
            (number of decimal places).

        Example:
            >>> @classmethod
            ... def get_col_precision_map(cls):
            ...     return {
            ...         "price": 2,
            ...         "percentage": 4,
            ...         "score": 1,
            ...     }
        """

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the CleaningDF and execute the cleaning pipeline.

        Creates a Polars DataFrame with NaN values automatically converted to
        null, then immediately executes the full cleaning pipeline. The schema
        is enforced from ``get_col_dtype_map()``.

        Args:
            *args: Positional arguments passed to ``pl.DataFrame`` constructor.
            **kwargs: Keyword arguments passed to ``pl.DataFrame`` constructor.

        Note:
            The following kwargs are automatically set and will override any
            user-provided values:
                - ``nan_to_null``: Always set to True
                - ``schema``: Set from ``get_col_dtype_map()``
                - ``data``: Replaced with renamed and filtered data
        """
        # create a temp df for standardization and accepting all ploars arg and kwargs
        temp_df = pl.DataFrame(*args, **kwargs)
        temp_df = self.rename_cols(temp_df)
        temp_df = self.drop_cols(temp_df)

        # enforce standard kwargs and create the final df
        kwargs["data"] = temp_df.to_dict(as_series=True)
        kwargs["nan_to_null"] = True
        kwargs["schema"] = self.get_col_dtype_map()
        self.df = pl.DataFrame(**kwargs)
        self.clean()

    @classmethod
    def get_col_names(cls) -> tuple[str, ...]:
        """Get the standardized column names from the dtype map.

        Returns:
            Tuple of standardized column names in the order they appear
            in ``get_col_dtype_map()``.
        """
        return tuple(cls.get_col_dtype_map().keys())

    def clean(self) -> None:
        """Execute the complete data cleaning pipeline.

        Applies all cleaning operations in the following order:
            1. Fill null values with defaults
            2. Convert columns to correct types and apply transformations
            3. Drop rows with all-null column subsets
            4. Handle duplicates by aggregating and removing
            5. Sort the DataFrame
            6. Validate data quality

        Note:
            Renaming and dropping columns are done during ``__init__`` before
            this method is called. This method is automatically called during
            initialization.
        """
        self.fill_nulls()
        self.convert_cols()
        self.drop_null_subsets()
        self.handle_duplicates()
        self.sort_cols()
        self.check()

    @classmethod
    def raise_on_missing_cols(
        cls,
        map_func: Callable[..., dict[str, Any]],
    ) -> None:
        """Validate that all required columns are present in a configuration map.

        Checks that the columns returned by ``map_func`` contain all columns
        defined in the schema. Raises KeyError if any required columns are
        missing from the map.

        Args:
            map_func: A callable that returns a dict with column names as keys.

        Raises:
            KeyError: If any required columns are missing from the map.
        """
        col_names = cls.get_col_names()
        missing_cols = set(col_names) - set(map_func().keys())
        if missing_cols:
            msg = f"Missing columns in {map_func}: {missing_cols}"
            raise KeyError(msg)

    def rename_cols(self, temp_df: pl.DataFrame) -> pl.DataFrame:
        """Rename columns from raw names to standardized names.

        Applies the reverse of ``get_rename_map()`` to rename columns from
        their raw input names to standardized names.

        Args:
            temp_df: The DataFrame with raw column names to rename.

        Returns:
            DataFrame with columns renamed to standardized names.

        Raises:
            KeyError: If any required columns are missing from the rename map.
        """
        self.raise_on_missing_cols(self.get_rename_map)
        return temp_df.rename(reverse_dict(self.get_rename_map()))

    def drop_cols(self, temp_df: pl.DataFrame) -> pl.DataFrame:
        """Drop columns not defined in the schema.

        Selects only the columns defined in ``get_col_names()``, removing any
        extra columns that may have been in the input data.

        Args:
            temp_df: The DataFrame to filter columns from.

        Returns:
            DataFrame containing only the columns defined in the schema.
        """
        return temp_df.select(self.get_col_names())

    def fill_nulls(self) -> None:
        """Fill null values with defaults from the fill null map.

        Replaces null values in each column with the corresponding fill value
        from ``get_fill_null_map()``.

        Raises:
            KeyError: If any columns are missing from the fill null map.
        """
        self.raise_on_missing_cols(self.get_fill_null_map)
        self.df = self.df.with_columns(
            [
                pl.col(col_name).fill_null(fill_value)
                for col_name, fill_value in self.get_fill_null_map().items()
            ]
        )

    def convert_cols(self) -> None:
        """Apply standard and custom column conversions.

        Orchestrates both standard conversions (string stripping, float
        rounding) and custom conversions defined in ``get_col_converter_map()``.

        Raises:
            KeyError: If any columns are missing from the converter map.
        """
        self.raise_on_missing_cols(self.get_col_converter_map)
        self.standard_convert_cols()
        self.custom_convert_cols()

    def standard_convert_cols(self) -> None:
        """Apply standard conversions based on data type.

        Automatically applies the following transformations:
            - ``pl.Utf8`` columns: Strip leading/trailing whitespace
            - ``pl.Float64`` columns: Round to precision using Kahan summation
        """
        for col_name, dtype in self.get_col_dtype_map().items():
            if dtype == pl.Utf8:
                converter = self.strip_col
            elif dtype == pl.Float64:
                converter = self.round_col
            else:
                continue
            self.df = self.df.with_columns(
                pl.col(col_name).map_batches(converter, return_dtype=dtype)
            )

    def custom_convert_cols(self) -> None:
        """Apply custom conversion functions to columns.

        Applies custom transformations from ``get_col_converter_map()`` to each
        column. Columns marked with ``skip_col_converter`` are skipped.
        """
        self.df = self.df.with_columns(
            [
                pl.col(col_name).map_batches(
                    converter, return_dtype=self.get_col_dtype_map()[col_name]
                )
                for col_name, converter in self.get_col_converter_map().items()
                if converter.__name__ != self.skip_col_converter.__name__  # ty:ignore[unresolved-attribute]
            ]
        )

    @classmethod
    def strip_col(cls, col: pl.Series) -> pl.Series:
        """Remove leading and trailing whitespace from a string column.

        Args:
            col: Polars Series of string type (``pl.Utf8``).

        Returns:
            Series with leading and trailing whitespace removed from each value.
        """
        return col.str.strip_chars()

    @classmethod
    def lower_col(cls, col: pl.Series) -> pl.Series:
        """Convert a string column to lowercase.

        Args:
            col: Polars Series of string type (``pl.Utf8``).

        Returns:
            Series with all characters converted to lowercase.
        """
        return col.str.to_lowercase()

    @classmethod
    def round_col(
        cls,
        col: pl.Series,
        precision: int | None = None,
        *,
        compensate: bool = True,
    ) -> pl.Series:
        """Round a float column to specified precision.

        Uses Kahan summation algorithm to compensate for floating-point
        rounding errors when ``compensate=True``, ensuring that the sum of
        rounded values matches the rounded sum of original values.

        Args:
            col: Polars Series of float type (``pl.Float64``).
            precision: Number of decimal places. If None, uses the value from
                ``get_col_precision_map()`` for this column.
            compensate: If True, use Kahan summation to reduce cumulative
                rounding errors. Defaults to True.

        Returns:
            Series with values rounded to the specified precision.

        Note:
            Kahan summation is slower than simple rounding but provides better
            accuracy for financial or scientific calculations where cumulative
            rounding errors matter.
        """
        if precision is None:
            precision = cls.get_col_precision_map()[str(col.name)]
        if not compensate:
            return col.round(precision)

        # compensate for rounding errors with kahan sum
        error = 0.0
        values = []
        for value in col.to_list():  # Ensure iteration over Python floats
            corrected = value + error
            rounded = round(corrected, precision)
            error = corrected - rounded
            values.append(rounded)

        return pl.Series(name=col.name, values=values, dtype=col.dtype)

    @classmethod
    def skip_col_converter(cls, _col: pl.Series) -> pl.Series:
        """Placeholder to skip custom conversion for a column.

        Use this method in ``get_col_converter_map()`` to indicate that a
        column should not have custom conversion applied. This method should
        never be actually called - it's only used as a marker.

        Args:
            _col: Unused. The column that would be converted.

        Raises:
            NotImplementedError: Always raised if this method is called.

        Example:
            >>> @classmethod
            ... def get_col_converter_map(cls):
            ...     return {
            ...         "email": lambda s: s.str.to_lowercase(),
            ...         "user_id": cls.skip_col_converter,  # No conversion
            ...     }
        """
        msg = (
            "skip_col_converter is just a flag to skip conversion for a column "
            "and should not be actually called."
        )
        raise NotImplementedError(msg)

    def drop_null_subsets(self) -> None:
        """Drop rows where all columns in a subset are null.

        Applies null-dropping rules defined in ``get_drop_null_subsets()``.
        If no subsets are defined, drops rows where all columns are null.
        """
        subsets = self.get_drop_null_subsets()
        if not subsets:
            self.df = self.df.drop_nulls()
            return
        for subset in subsets:
            self.df = self.df.drop_nulls(subset=subset)

    def handle_duplicates(self) -> None:
        """Remove duplicate rows and aggregate specified columns.

        For each uniqueness subset defined in ``get_unique_subsets()``:
            1. Sum values in columns specified by ``get_add_on_duplicate_cols()``
            2. Keep only the first row of each duplicate group

        Example:
            If two rows have the same (user_id, date) and values 1 and 2 in
            the 'quantity' column, the result will have one row with
            quantity=3.
        """
        for subset in self.get_unique_subsets():
            for col in self.get_add_on_duplicate_cols():
                self.df = self.df.with_columns(pl.col(col).sum().over(subset))
            self.df = self.df.unique(subset=subset, keep="first")

    def sort_cols(self) -> None:
        """Sort the DataFrame by columns and directions from get_sort_cols().

        Applies multi-column sorting with per-column sort direction
        (ascending or descending) as defined in ``get_sort_cols()``.
        """
        cols, desc = zip(*self.get_sort_cols(), strict=True)
        if not cols:
            return
        self.df = self.df.sort(cols, descending=desc)

    def check(self) -> None:
        """Validate data quality after cleaning.

        Runs all validation checks in order:
            1. Correct data types for all columns
            2. No null values in required columns
            3. No NaN values in float columns

        This method is called automatically at the end of the ``clean()``
        pipeline.

        Raises:
            TypeError: If any column has an incorrect data type.
            ValueError: If required columns contain nulls or float columns
                contain NaN values.
        """
        self.check_correct_dtypes()
        self.check_no_null_cols()
        self.check_no_nan()

    def check_correct_dtypes(self) -> None:
        """Validate that all columns have their expected data types.

        Compares the actual DataFrame schema against the expected types
        defined in ``get_col_dtype_map()``.

        Raises:
            TypeError: If any column's actual type doesn't match the expected
                type from the schema.
        """
        schema = self.df.schema
        col_dtype_map = self.get_col_dtype_map()
        for col, dtype in col_dtype_map.items():
            schema_dtype = schema[col]
            if schema_dtype != dtype:
                msg = f"Expected dtype {dtype} for column {col}, got {schema_dtype}"
                raise TypeError(msg)

    def check_no_null_cols(self) -> None:
        """Validate that required columns contain no null values.

        Checks all columns defined in ``get_no_null_cols()`` for null values.

        Raises:
            ValueError: If any column in ``get_no_null_cols()`` contains null
                values.
        """
        no_null_cols = self.get_no_null_cols()
        # Use a single select to check all columns at once
        null_flags = self.df.select(
            [pl.col(col).is_null().any() for col in no_null_cols]
        )
        # Iterate over columns and check if any have nulls
        for col in no_null_cols:
            if null_flags[col].item():
                msg = f"Null values found in column: {col}"
                raise ValueError(msg)

    def check_no_nan(self) -> None:
        """Validate that float columns contain no NaN values.

        Checks all columns with float data types (``pl.Float64``, etc.) for
        NaN values.

        Raises:
            ValueError: If any float column contains NaN values.
        """
        float_cols = [
            col
            for col, dtype in self.get_col_dtype_map().items()
            if issubclass(dtype, FloatType)
        ]
        has_nan = self.df.select(
            pl.any_horizontal(pl.col(float_cols).is_nan().any())
        ).item()
        if has_nan:
            msg = "NaN values found in the dataframe"
            raise ValueError(msg)
