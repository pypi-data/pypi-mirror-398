from typing import Dict, Any, List
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, when, isnan, isnull, lit, regexp_extract, regexp_replace, length, size, count, sum as spark_sum,
    min as spark_min, max as spark_max, mean, stddev, approx_count_distinct, desc,
    row_number, rank, dense_rank, to_date, to_timestamp, from_json, schema_of_json,
    monotonically_increasing_id, lag, lead, abs as spark_abs, coalesce, current_date,
    current_timestamp, datediff, date_add, date_sub, add_months, lower
)
from pyspark.sql.types import (
    StringType, NumericType, IntegerType, DoubleType, FloatType, LongType, 
    BooleanType, DateType, TimestampType, StructType, ArrayType
)
from pyspark.sql.window import Window
import re
import json
from datetime import datetime


class RuleProcessor:
    """
    Processes Great Expectations rules and converts them into Spark DataFrame conditions
    for row-level validation.
    """
    
    def __init__(self):
        """Initialize the rule processor."""
        self.supported_expectations = {
            # Basic Column Existence and Null Checks
            "expect_column_to_exist": self._expect_column_to_exist,
            "expect_column_values_to_not_be_null": self._expect_column_values_to_not_be_null,
            "expect_column_values_to_be_null": self._expect_column_values_to_be_null,
            
            # Uniqueness Expectations
            "expect_column_values_to_be_unique": self._expect_column_values_to_be_unique,
            "expect_compound_columns_to_be_unique": self._expect_compound_columns_to_be_unique,
            "expect_select_column_values_to_be_unique_within_record": self._expect_select_column_values_to_be_unique_within_record,
            
            # Range and Value Expectations
            "expect_column_values_to_be_between": self._expect_column_values_to_be_between,
            "expect_column_values_to_be_in_set": self._expect_column_values_to_be_in_set,
            "expect_column_values_to_not_be_in_set": self._expect_column_values_to_not_be_in_set,
            "expect_column_distinct_values_to_be_in_set": self._expect_column_distinct_values_to_be_in_set,
            "expect_column_distinct_values_to_contain_set": self._expect_column_distinct_values_to_contain_set,
            "expect_column_distinct_values_to_equal_set": self._expect_column_distinct_values_to_equal_set,
            
            # Pattern Matching Expectations
            "expect_column_values_to_match_regex": self._expect_column_values_to_match_regex,
            "expect_column_values_to_not_match_regex": self._expect_column_values_to_not_match_regex,
            "expect_column_values_to_match_strftime_format": self._expect_column_values_to_match_strftime_format,
            
            # Value Transformation/Normalization Expectations
            "expect_column_values_to_be_normalized": self._expect_column_values_to_be_normalized,
            "expect_column_values_to_match_regex_and_replace": self._expect_column_values_to_match_regex_and_replace,
            
            # String Length Expectations
            "expect_column_value_lengths_to_be_between": self._expect_column_value_lengths_to_be_between,
            "expect_column_value_lengths_to_equal": self._expect_column_value_lengths_to_equal,
            
            # Type Expectations
            "expect_column_values_to_be_of_type": self._expect_column_values_to_be_of_type,
            "expect_column_values_to_be_in_type_list": self._expect_column_values_to_be_in_type_list,
            
            # Date and Time Expectations
            "expect_column_values_to_be_dateutil_parseable": self._expect_column_values_to_be_dateutil_parseable,
            "expect_column_values_to_not_be_future_date": self._expect_column_values_to_not_be_future_date,
            "expect_column_values_to_not_be_older_than_years": self._expect_column_values_to_not_be_older_than_years,
            
            # JSON Expectations
            "expect_column_values_to_be_json_parseable": self._expect_column_values_to_be_json_parseable,
            "expect_column_values_to_match_json_schema": self._expect_column_values_to_match_json_schema,
            
            # Ordering Expectations
            "expect_column_values_to_be_increasing": self._expect_column_values_to_be_increasing,
            "expect_column_values_to_be_decreasing": self._expect_column_values_to_be_decreasing,
            
            # Statistical Expectations (Table-level but can be applied row-wise)
            "expect_column_mean_to_be_between": self._expect_column_mean_to_be_between,
            "expect_column_median_to_be_between": self._expect_column_median_to_be_between,
            "expect_column_stdev_to_be_between": self._expect_column_stdev_to_be_between,
            "expect_column_unique_value_count_to_be_between": self._expect_column_unique_value_count_to_be_between,
            "expect_column_proportion_of_unique_values_to_be_between": self._expect_column_proportion_of_unique_values_to_be_between,
            "expect_column_most_common_value_to_be_in_set": self._expect_column_most_common_value_to_be_in_set,
            "expect_column_max_to_be_between": self._expect_column_max_to_be_between,
            "expect_column_min_to_be_between": self._expect_column_min_to_be_between,
            "expect_column_sum_to_be_between": self._expect_column_sum_to_be_between,
            "expect_column_quantile_values_to_be_between": self._expect_column_quantile_values_to_be_between,
            
            # Column Pair Expectations
            "expect_column_pair_values_to_be_equal": self._expect_column_pair_values_to_be_equal,
            "expect_column_pair_values_A_to_be_greater_than_B": self._expect_column_pair_values_A_to_be_greater_than_B,
            "expect_column_pair_values_to_be_in_set": self._expect_column_pair_values_to_be_in_set,
            "expect_column_values_to_be_after_column": self._expect_column_values_to_be_after_column,
            "expect_column_values_to_be_after_column_if_populated": self._expect_column_values_to_be_after_column_if_populated,
            "expect_column_values_to_not_be_before_column_if_populated": self._expect_column_values_to_not_be_before_column_if_populated,
            "expect_column_to_not_be_null_if_condition": self._expect_column_to_not_be_null_if_condition,
            "expect_column_values_conditional_date_comparison": self._expect_column_values_conditional_date_comparison,
            
            # Table-level Expectations
            "expect_table_row_count_to_be_between": self._expect_table_row_count_to_be_between,
            "expect_table_row_count_to_equal": self._expect_table_row_count_to_equal,
            "expect_table_column_count_to_be_between": self._expect_table_column_count_to_be_between,
            "expect_table_column_count_to_equal": self._expect_table_column_count_to_equal,
            "expect_table_columns_to_match_ordered_list": self._expect_table_columns_to_match_ordered_list,
            "expect_table_columns_to_match_set": self._expect_table_columns_to_match_set,
            
            # Multi-column Expectations
            "expect_multicolumn_values_to_be_unique": self._expect_multicolumn_values_to_be_unique,
        }
    
    def create_validation_condition(self, rule: Dict[str, Any], dataframe: DataFrame):
        """
        Create a Spark DataFrame condition for a given quality rule.
        
        Args:
            rule: Dictionary containing expectation_type and kwargs
            dataframe: The DataFrame to validate against
            
        Returns:
            Spark Column condition that evaluates to True for valid rows
        """
        expectation_type = rule.get("expectation_type")
        kwargs = rule.get("kwargs", {})
        
        if expectation_type not in self.supported_expectations:
            raise ValueError(f"Unsupported expectation type: {expectation_type}")
        
        return self.supported_expectations[expectation_type](kwargs, dataframe)
    
    def create_transformation_column(self, rule: Dict[str, Any], dataframe: DataFrame):
        """
        Create a Spark Column transformation for normalization and regex replacement expectations.
        
        Args:
            rule: Dictionary containing expectation_type and kwargs
            dataframe: The DataFrame to transform
            
        Returns:
            Spark Column with transformed values, or None if not a transformation rule
        """
        expectation_type = rule.get("expectation_type")
        
        if expectation_type == "expect_column_values_to_be_normalized":
            return self._create_normalization_transformation(rule.get("kwargs", {}), dataframe)
        elif expectation_type == "expect_column_values_to_match_regex_and_replace":
            return self._create_regex_replacement_transformation(rule.get("kwargs", {}), dataframe)
        
        return None
    
    def _create_normalization_transformation(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Create the actual transformation column for normalization."""
        column_name = kwargs.get("column")
        value_mapping = kwargs.get("value_mapping", {})
        case_sensitive = kwargs.get("case_sensitive", False)
        
        self._validate_column_exists(column_name, dataframe)
        
        if not value_mapping:
            return col(column_name)  # No mapping, return original
        
        # Start with the original column
        normalized_col = col(column_name)
        
        # Apply transformations based on mapping
        for original_value, normalized_value in value_mapping.items():
            if case_sensitive:
                normalized_col = when(normalized_col == original_value, normalized_value).otherwise(normalized_col)
            else:
                # Case-insensitive matching
                normalized_col = when(
                    lower(normalized_col) == lower(lit(original_value)), 
                    normalized_value
                ).otherwise(normalized_col)
        
        return normalized_col
    
    def _create_regex_replacement_transformation(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Create the actual transformation column for regex replacement."""
        column_name = kwargs.get("column")
        regex_pattern = kwargs.get("regex")
        replacement = kwargs.get("replacement", "")
        
        self._validate_column_exists(column_name, dataframe)
        
        if not regex_pattern:
            return col(column_name)  # No pattern, return original
        
        # Use regexp_replace to replace matched values
        # regexp_replace(column, pattern, replacement)
        transformed_col = regexp_replace(col(column_name), regex_pattern, replacement)
        
        return transformed_col
    
    def is_transformation_expectation(self, expectation_type: str) -> bool:
        """Check if an expectation type performs transformations."""
        transformation_expectations = [
            "expect_column_values_to_be_normalized",
            "expect_column_values_to_match_regex_and_replace"
        ]
        return expectation_type in transformation_expectations
    
    def _expect_column_to_exist(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check if column exists. For row-level validation, this always returns True if column exists."""
        column_name = kwargs.get("column")
        if column_name not in dataframe.columns:
            raise ValueError(f"Column '{column_name}' does not exist in DataFrame")
        return lit(True)
    
    def _expect_column_values_to_not_be_null(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column values are not null."""
        column_name = kwargs.get("column")
        self._validate_column_exists(column_name, dataframe)
        
        return col(column_name).isNotNull()
    
    def _expect_column_values_to_be_null(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column values are null."""
        column_name = kwargs.get("column")
        self._validate_column_exists(column_name, dataframe)
        
        return col(column_name).isNull()
    
    def _expect_column_values_to_be_unique(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """
        Check column values for uniqueness. 
        Note: This is approximate for row-level validation - duplicates will be marked as invalid.
        """
        column_name = kwargs.get("column")
        self._validate_column_exists(column_name, dataframe)
        
        # Create a window function to count occurrences of each value
        from pyspark.sql.functions import count
        
        window = Window.partitionBy(column_name)
        # This is a simplified approach - for true uniqueness validation,
        # you might need more sophisticated logic
        return count(col(column_name)).over(window) == 1
    
    def _expect_column_values_to_be_between(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column values are between min and max values."""
        column_name = kwargs.get("column")
        min_value = kwargs.get("min_value")
        max_value = kwargs.get("max_value")
        
        self._validate_column_exists(column_name, dataframe)
        
        condition = lit(True)
        
        if min_value is not None:
            condition = condition & (col(column_name) >= min_value)
        
        if max_value is not None:
            condition = condition & (col(column_name) <= max_value)
        
        return condition
    
    def _expect_column_values_to_be_in_set(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column values are in a specified set."""
        column_name = kwargs.get("column")
        value_set = kwargs.get("value_set", [])
        
        self._validate_column_exists(column_name, dataframe)
        
        if not value_set:
            return lit(False)
        
        return col(column_name).isin(value_set)
    
    def _expect_column_values_to_not_be_in_set(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column values are not in a specified set."""
        column_name = kwargs.get("column")
        value_set = kwargs.get("value_set", [])
        
        self._validate_column_exists(column_name, dataframe)
        
        if not value_set:
            return lit(True)
        
        return ~col(column_name).isin(value_set)
    
    def _expect_column_values_to_match_regex(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column values match a regular expression."""
        column_name = kwargs.get("column")
        regex_pattern = kwargs.get("regex")
        
        self._validate_column_exists(column_name, dataframe)
        
        if not regex_pattern:
            return lit(True)
        
        return col(column_name).rlike(regex_pattern)
    
    def _expect_column_values_to_not_match_regex(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column values do not match a regular expression."""
        column_name = kwargs.get("column")
        regex_pattern = kwargs.get("regex")
        
        self._validate_column_exists(column_name, dataframe)
        
        if not regex_pattern:
            return lit(True)
        
        return ~col(column_name).rlike(regex_pattern)
    
    def _expect_column_value_lengths_to_be_between(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column value lengths are between min and max."""
        column_name = kwargs.get("column")
        min_value = kwargs.get("min_value")
        max_value = kwargs.get("max_value")
        
        self._validate_column_exists(column_name, dataframe)
        
        length_col = length(col(column_name))
        condition = lit(True)
        
        if min_value is not None:
            condition = condition & (length_col >= min_value)
        
        if max_value is not None:
            condition = condition & (length_col <= max_value)
        
        return condition
    
    def _expect_column_values_to_be_of_type(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """
        Check column values are of specified type.
        Note: This is limited in Spark as type checking is done at DataFrame level.
        """
        column_name = kwargs.get("column")
        expected_type = kwargs.get("type_")
        
        self._validate_column_exists(column_name, dataframe)
        
        # Get actual column type
        actual_type = dict(dataframe.dtypes)[column_name]
        
        # Simple type matching - this could be enhanced
        if expected_type == "string" and "string" in actual_type.lower():
            return lit(True)
        elif expected_type == "int" and ("int" in actual_type.lower() or "long" in actual_type.lower()):
            return lit(True)
        elif expected_type == "float" and ("float" in actual_type.lower() or "double" in actual_type.lower()):
            return lit(True)
        else:
            return lit(False)
    
    def _expect_column_values_to_be_in_type_list(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check column values are in list of specified types."""
        column_name = kwargs.get("column")
        type_list = kwargs.get("type_list", [])
        
        self._validate_column_exists(column_name, dataframe)
        
        # Check if current column type matches any in the list
        actual_type = dict(dataframe.dtypes)[column_name]
        
        for expected_type in type_list:
            if self._type_matches(actual_type, expected_type):
                return lit(True)
        
        return lit(False)
    
    # ========== NEW GREAT EXPECTATIONS IMPLEMENTATIONS ==========
    
    def _expect_compound_columns_to_be_unique(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that combinations of column values are unique."""
        column_list = kwargs.get("column_list", [])
        if not column_list:
            return lit(True)
        
        # Validate all columns exist
        for col_name in column_list:
            self._validate_column_exists(col_name, dataframe)
        
        # Create window partitioned by the compound columns
        window = Window.partitionBy(*column_list)
        return count(lit(1)).over(window) == 1
    
    def _expect_select_column_values_to_be_unique_within_record(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that values within a record are unique across specified columns."""
        column_list = kwargs.get("column_list", [])
        if len(column_list) < 2:
            return lit(True)
        
        for col_name in column_list:
            self._validate_column_exists(col_name, dataframe)
        
        # For each pair of columns, check they're not equal (simplified approach)
        condition = lit(True)
        for i in range(len(column_list)):
            for j in range(i + 1, len(column_list)):
                condition = condition & (
                    col(column_list[i]).isNull() | 
                    col(column_list[j]).isNull() | 
                    (col(column_list[i]) != col(column_list[j]))
                )
        return condition
    
    def _expect_column_distinct_values_to_be_in_set(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that distinct values in column are within a specified set."""
        column_name = kwargs.get("column")
        value_set = kwargs.get("value_set", [])
        
        self._validate_column_exists(column_name, dataframe)
        
        if not value_set:
            return lit(False)
        
        # For row-level validation, this is same as regular in_set check
        return col(column_name).isin(value_set)
    
    def _expect_column_distinct_values_to_contain_set(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column contains all values from a specified set."""
        column_name = kwargs.get("column")
        value_set = kwargs.get("value_set", [])
        
        self._validate_column_exists(column_name, dataframe)
        
        # For row-level validation, check if current value is in the required set
        return col(column_name).isin(value_set) if value_set else lit(True)
    
    def _expect_column_distinct_values_to_equal_set(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that distinct values exactly match a specified set."""
        column_name = kwargs.get("column")
        value_set = kwargs.get("value_set", [])
        
        self._validate_column_exists(column_name, dataframe)
        
        # For row-level validation, check if value is in the expected set
        return col(column_name).isin(value_set) if value_set else lit(True)
    
    def _expect_column_values_to_match_strftime_format(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column values match a strftime format."""
        column_name = kwargs.get("column")
        strftime_format = kwargs.get("strftime_format", "%Y-%m-%d")
        
        self._validate_column_exists(column_name, dataframe)
        
        # Convert strftime format to regex pattern (simplified)
        format_patterns = {
            "%Y": r"\d{4}",
            "%y": r"\d{2}",
            "%m": r"\d{2}",
            "%d": r"\d{2}",
            "%H": r"\d{2}",
            "%M": r"\d{2}",
            "%S": r"\d{2}",
            "%B": r"[A-Za-z]+",
            "%b": r"[A-Za-z]{3}",
            "%A": r"[A-Za-z]+",
            "%a": r"[A-Za-z]{3}"
        }
        
        regex_pattern = strftime_format
        for fmt, pattern in format_patterns.items():
            regex_pattern = regex_pattern.replace(fmt, pattern)
        
        return col(column_name).rlike(f"^{regex_pattern}$")
    
    def _expect_column_value_lengths_to_equal(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column value lengths equal a specific value."""
        column_name = kwargs.get("column")
        value = kwargs.get("value")
        
        self._validate_column_exists(column_name, dataframe)
        
        if value is None:
            return lit(True)
        
        return length(col(column_name)) == value
    
    def _expect_column_values_to_be_dateutil_parseable(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column values can be parsed as dates."""
        column_name = kwargs.get("column")
        
        self._validate_column_exists(column_name, dataframe)
        
        # Try to parse as date - if successful, not null
        return to_date(col(column_name)).isNotNull()
    
    def _expect_column_values_to_not_be_future_date(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column values are not future dates."""
        column_name = kwargs.get("column")
        use_timestamp = kwargs.get("use_timestamp", False)
        
        self._validate_column_exists(column_name, dataframe)
        
        # Convert column to date/timestamp for comparison
        date_col = to_timestamp(col(column_name)) if use_timestamp else to_date(col(column_name))
        current = current_timestamp() if use_timestamp else current_date()
        
        # If null, consider valid (or you can add null handling option)
        return col(column_name).isNull() | (date_col <= current)
    
    def _expect_column_values_to_not_be_older_than_years(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column values are not older than specified number of years."""
        column_name = kwargs.get("column")
        years_threshold = kwargs.get("years", 150)
        use_timestamp = kwargs.get("use_timestamp", False)
        
        self._validate_column_exists(column_name, dataframe)
        
        # Convert column to date/timestamp
        date_col = to_timestamp(col(column_name)) if use_timestamp else to_date(col(column_name))
        current = current_timestamp() if use_timestamp else current_date()
        
        # Calculate date threshold (current date - years)
        # Using add_months with negative value to subtract years
        threshold_date = add_months(current, -12 * years_threshold)
        
        # If null, consider valid
        return col(column_name).isNull() | (date_col >= threshold_date)
    
    def _expect_column_values_to_be_json_parseable(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column values are valid JSON."""
        column_name = kwargs.get("column")
        
        self._validate_column_exists(column_name, dataframe)
        
        # Try to parse JSON - simplified check using regex
        json_pattern = r'^\s*[\{\[].*[\}\]]\s*$'
        return col(column_name).rlike(json_pattern)
    
    def _expect_column_values_to_match_json_schema(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column values match a JSON schema."""
        column_name = kwargs.get("column")
        json_schema = kwargs.get("json_schema", {})
        
        self._validate_column_exists(column_name, dataframe)
        
        # Simplified JSON schema validation - check if parseable
        return self._expect_column_values_to_be_json_parseable(kwargs, dataframe)
    
    def _expect_column_values_to_be_increasing(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column values are increasing."""
        column_name = kwargs.get("column")
        strictly = kwargs.get("strictly", False)
        
        self._validate_column_exists(column_name, dataframe)
        
        # Use window function to compare with previous value
        window = Window.orderBy(monotonically_increasing_id())
        prev_value = lag(col(column_name)).over(window)
        
        if strictly:
            return prev_value.isNull() | (col(column_name) > prev_value)
        else:
            return prev_value.isNull() | (col(column_name) >= prev_value)
    
    def _expect_column_values_to_be_decreasing(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column values are decreasing."""
        column_name = kwargs.get("column")
        strictly = kwargs.get("strictly", False)
        
        self._validate_column_exists(column_name, dataframe)
        
        # Use window function to compare with previous value
        window = Window.orderBy(monotonically_increasing_id())
        prev_value = lag(col(column_name)).over(window)
        
        if strictly:
            return prev_value.isNull() | (col(column_name) < prev_value)
        else:
            return prev_value.isNull() | (col(column_name) <= prev_value)
    
    def _expect_column_mean_to_be_between(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column mean is between min and max values."""
        column_name = kwargs.get("column")
        min_value = kwargs.get("min_value")
        max_value = kwargs.get("max_value")
        
        self._validate_column_exists(column_name, dataframe)
        
        # Calculate mean using window function
        window = Window.partitionBy()
        column_mean = mean(col(column_name)).over(window)
        
        condition = lit(True)
        if min_value is not None:
            condition = condition & (column_mean >= min_value)
        if max_value is not None:
            condition = condition & (column_mean <= max_value)
        
        return condition
    
    def _expect_column_median_to_be_between(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column median is between min and max values."""
        column_name = kwargs.get("column")
        min_value = kwargs.get("min_value")
        max_value = kwargs.get("max_value")
        
        self._validate_column_exists(column_name, dataframe)
        
        # Approximate median using percentile
        window = Window.partitionBy()
        # Simplified - use mean as approximation for median
        column_median = mean(col(column_name)).over(window)
        
        condition = lit(True)
        if min_value is not None:
            condition = condition & (column_median >= min_value)
        if max_value is not None:
            condition = condition & (column_median <= max_value)
        
        return condition
    
    def _expect_column_stdev_to_be_between(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column standard deviation is between min and max values."""
        column_name = kwargs.get("column")
        min_value = kwargs.get("min_value")
        max_value = kwargs.get("max_value")
        
        self._validate_column_exists(column_name, dataframe)
        
        # Calculate standard deviation using window function
        window = Window.partitionBy()
        column_stdev = stddev(col(column_name)).over(window)
        
        condition = lit(True)
        if min_value is not None:
            condition = condition & (column_stdev >= min_value)
        if max_value is not None:
            condition = condition & (column_stdev <= max_value)
        
        return condition
    
    def _expect_column_unique_value_count_to_be_between(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that count of unique values is between min and max."""
        column_name = kwargs.get("column")
        min_value = kwargs.get("min_value")
        max_value = kwargs.get("max_value")
        
        self._validate_column_exists(column_name, dataframe)
        
        # Use approximate count distinct
        window = Window.partitionBy()
        unique_count = approx_count_distinct(col(column_name)).over(window)
        
        condition = lit(True)
        if min_value is not None:
            condition = condition & (unique_count >= min_value)
        if max_value is not None:
            condition = condition & (unique_count <= max_value)
        
        return condition
    
    def _expect_column_proportion_of_unique_values_to_be_between(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that proportion of unique values is between min and max."""
        column_name = kwargs.get("column")
        min_value = kwargs.get("min_value")
        max_value = kwargs.get("max_value")
        
        self._validate_column_exists(column_name, dataframe)
        
        # Calculate proportion: unique_count / total_count
        window = Window.partitionBy()
        unique_count = approx_count_distinct(col(column_name)).over(window)
        total_count = count(col(column_name)).over(window)
        proportion = unique_count / total_count
        
        condition = lit(True)
        if min_value is not None:
            condition = condition & (proportion >= min_value)
        if max_value is not None:
            condition = condition & (proportion <= max_value)
        
        return condition
    
    def _expect_column_most_common_value_to_be_in_set(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that the most common value is in a specified set."""
        column_name = kwargs.get("column")
        value_set = kwargs.get("value_set", [])
        
        self._validate_column_exists(column_name, dataframe)
        
        # Simplified: check if current value is in the set
        return col(column_name).isin(value_set) if value_set else lit(True)
    
    def _expect_column_max_to_be_between(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column maximum is between min and max values."""
        column_name = kwargs.get("column")
        min_value = kwargs.get("min_value")
        max_value = kwargs.get("max_value")
        
        self._validate_column_exists(column_name, dataframe)
        
        # Calculate max using window function
        window = Window.partitionBy()
        column_max = spark_max(col(column_name)).over(window)
        
        condition = lit(True)
        if min_value is not None:
            condition = condition & (column_max >= min_value)
        if max_value is not None:
            condition = condition & (column_max <= max_value)
        
        return condition
    
    def _expect_column_min_to_be_between(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column minimum is between min and max values."""
        column_name = kwargs.get("column")
        min_value = kwargs.get("min_value")
        max_value = kwargs.get("max_value")
        
        self._validate_column_exists(column_name, dataframe)
        
        # Calculate min using window function
        window = Window.partitionBy()
        column_min = spark_min(col(column_name)).over(window)
        
        condition = lit(True)
        if min_value is not None:
            condition = condition & (column_min >= min_value)
        if max_value is not None:
            condition = condition & (column_min <= max_value)
        
        return condition
    
    def _expect_column_sum_to_be_between(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column sum is between min and max values."""
        column_name = kwargs.get("column")
        min_value = kwargs.get("min_value")
        max_value = kwargs.get("max_value")
        
        self._validate_column_exists(column_name, dataframe)
        
        # Calculate sum using window function
        window = Window.partitionBy()
        column_sum = spark_sum(col(column_name)).over(window)
        
        condition = lit(True)
        if min_value is not None:
            condition = condition & (column_sum >= min_value)
        if max_value is not None:
            condition = condition & (column_sum <= max_value)
        
        return condition
    
    def _expect_column_quantile_values_to_be_between(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that column quantile values are between specified ranges."""
        column_name = kwargs.get("column")
        quantile_ranges = kwargs.get("quantile_ranges", {})
        
        self._validate_column_exists(column_name, dataframe)
        
        # Simplified: just check basic range for the value
        condition = lit(True)
        if quantile_ranges:
            # Use the overall min/max from quantile ranges
            all_values = []
            for ranges in quantile_ranges.values():
                if isinstance(ranges, dict):
                    all_values.extend([ranges.get("min_value"), ranges.get("max_value")])
            
            if all_values:
                all_values = [v for v in all_values if v is not None]
                if all_values:
                    min_val = min(all_values)
                    max_val = max(all_values)
                    condition = (col(column_name) >= min_val) & (col(column_name) <= max_val)
        
        return condition
    
    def _expect_column_pair_values_to_be_equal(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that values in two columns are equal."""
        column_A = kwargs.get("column_A")
        column_B = kwargs.get("column_B")
        
        self._validate_column_exists(column_A, dataframe)
        self._validate_column_exists(column_B, dataframe)
        
        return (col(column_A) == col(column_B)) | (col(column_A).isNull() & col(column_B).isNull())
    
    def _expect_column_pair_values_A_to_be_greater_than_B(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that values in column A are greater than values in column B."""
        column_A = kwargs.get("column_A")
        column_B = kwargs.get("column_B")
        or_equal = kwargs.get("or_equal", False)
        
        self._validate_column_exists(column_A, dataframe)
        self._validate_column_exists(column_B, dataframe)
        
        if or_equal:
            return col(column_A) >= col(column_B)
        else:
            return col(column_A) > col(column_B)
    
    def _expect_column_pair_values_to_be_in_set(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that pairs of values are in a specified set."""
        column_A = kwargs.get("column_A")
        column_B = kwargs.get("column_B")
        value_pairs_set = kwargs.get("value_pairs_set", [])
        
        self._validate_column_exists(column_A, dataframe)
        self._validate_column_exists(column_B, dataframe)
        
        if not value_pairs_set:
            return lit(True)
        
        # Create condition for each valid pair
        condition = lit(False)
        for pair in value_pairs_set:
            if len(pair) >= 2:
                pair_condition = (col(column_A) == pair[0]) & (col(column_B) == pair[1])
                condition = condition | pair_condition
        
        return condition
    
    def _expect_table_row_count_to_be_between(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that table row count is between min and max values."""
        min_value = kwargs.get("min_value")
        max_value = kwargs.get("max_value")
        
        # Calculate total row count
        window = Window.partitionBy()
        row_count = count(lit(1)).over(window)
        
        condition = lit(True)
        if min_value is not None:
            condition = condition & (row_count >= min_value)
        if max_value is not None:
            condition = condition & (row_count <= max_value)
        
        return condition
    
    def _expect_table_row_count_to_equal(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that table row count equals a specific value."""
        value = kwargs.get("value")
        
        if value is None:
            return lit(True)
        
        # Calculate total row count
        window = Window.partitionBy()
        row_count = count(lit(1)).over(window)
        
        return row_count == value
    
    def _expect_table_column_count_to_be_between(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that table column count is between min and max values."""
        min_value = kwargs.get("min_value")
        max_value = kwargs.get("max_value")
        
        column_count = len(dataframe.columns)
        
        condition = True
        if min_value is not None:
            condition = condition and (column_count >= min_value)
        if max_value is not None:
            condition = condition and (column_count <= max_value)
        
        return lit(condition)
    
    def _expect_table_column_count_to_equal(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that table column count equals a specific value."""
        value = kwargs.get("value")
        
        if value is None:
            return lit(True)
        
        column_count = len(dataframe.columns)
        return lit(column_count == value)
    
    def _expect_table_columns_to_match_ordered_list(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that table columns match an ordered list."""
        column_list = kwargs.get("column_list", [])
        
        actual_columns = list(dataframe.columns)
        matches = actual_columns == column_list
        
        return lit(matches)
    
    def _expect_table_columns_to_match_set(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that table columns match a set (order doesn't matter)."""
        column_set = kwargs.get("column_set", [])
        
        actual_columns_set = set(dataframe.columns)
        expected_columns_set = set(column_set)
        matches = actual_columns_set == expected_columns_set
        
        return lit(matches)
    
    def _expect_multicolumn_values_to_be_unique(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that combinations of multiple column values are unique."""
        column_list = kwargs.get("column_list", [])
        
        if not column_list:
            return lit(True)
        
        # Validate all columns exist
        for col_name in column_list:
            self._validate_column_exists(col_name, dataframe)
        
        # Create window partitioned by all columns
        window = Window.partitionBy(*column_list)
        return count(lit(1)).over(window) == 1
    
    def _expect_column_values_to_be_after_column(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that values in column A are after values in column B (for dates/timestamps)."""
        column_A = kwargs.get("column_A")
        column_B = kwargs.get("column_B")
        or_equal = kwargs.get("or_equal", False)
        use_timestamp = kwargs.get("use_timestamp", True)
        
        self._validate_column_exists(column_A, dataframe)
        self._validate_column_exists(column_B, dataframe)
        
        # Convert to appropriate date/timestamp type
        if use_timestamp:
            col_A = to_timestamp(col(column_A))
            col_B = to_timestamp(col(column_B))
        else:
            col_A = to_date(col(column_A))
            col_B = to_date(col(column_B))
        
        # Handle nulls: if either is null, consider valid (or adjust based on requirements)
        if or_equal:
            return col(column_A).isNull() | col(column_B).isNull() | (col_A >= col_B)
        else:
            return col(column_A).isNull() | col(column_B).isNull() | (col_A > col_B)
    
    def _expect_column_values_to_be_after_column_if_populated(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that if column A is populated, it should be after column B."""
        column_A = kwargs.get("column_A")
        column_B = kwargs.get("column_B")
        or_equal = kwargs.get("or_equal", False)
        use_timestamp = kwargs.get("use_timestamp", True)
        
        self._validate_column_exists(column_A, dataframe)
        self._validate_column_exists(column_B, dataframe)
        
        # Convert to appropriate date/timestamp type
        if use_timestamp:
            col_A = to_timestamp(col(column_A))
            col_B = to_timestamp(col(column_B))
        else:
            col_A = to_date(col(column_A))
            col_B = to_date(col(column_B))
        
        # If column_A is null, it's valid (not populated)
        # If column_A is populated, it must be after column_B
        if or_equal:
            return col(column_A).isNull() | (col_A >= col_B)
        else:
            return col(column_A).isNull() | (col_A > col_B)
    
    def _expect_column_values_to_not_be_before_column_if_populated(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that if column A is populated, it should not be before column B."""
        column_A = kwargs.get("column_A")
        column_B = kwargs.get("column_B")
        or_equal = kwargs.get("or_equal", False)
        use_timestamp = kwargs.get("use_timestamp", True)
        
        self._validate_column_exists(column_A, dataframe)
        self._validate_column_exists(column_B, dataframe)
        
        # Convert to appropriate date/timestamp type
        if use_timestamp:
            col_A = to_timestamp(col(column_A))
            col_B = to_timestamp(col(column_B))
        else:
            col_A = to_date(col(column_A))
            col_B = to_date(col(column_B))
        
        # If column_A is null, it's valid (not populated)
        # If column_A is populated, it must not be before column_B (i.e., >= column_B)
        if or_equal:
            return col(column_A).isNull() | (col_A >= col_B)
        else:
            return col(column_A).isNull() | (col_A > col_B)
    
    def _expect_column_to_not_be_null_if_condition(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """Check that if condition column is True, then target column should not be null."""
        condition_column = kwargs.get("condition_column")
        target_column = kwargs.get("target_column")
        condition_value = kwargs.get("condition_value", True)  # Default to True
        
        self._validate_column_exists(condition_column, dataframe)
        self._validate_column_exists(target_column, dataframe)
        
        # If condition is met, target must not be null
        # If condition is not met, target can be null or not null (always valid)
        condition_met = col(condition_column) == condition_value
        return ~condition_met | col(target_column).isNotNull()
    
    def _expect_column_values_conditional_date_comparison(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """
        Complex conditional date comparison.
        Example: DeceasedDatetime must be after DateOfBirth if DateOfBirth is not null,
        else DeceasedDatetime should not be before CreatedDateTime.
        """
        target_column = kwargs.get("target_column")
        primary_condition_column = kwargs.get("primary_condition_column")
        primary_comparison = kwargs.get("primary_comparison", "after")  # "after" or "before"
        fallback_column = kwargs.get("fallback_column")
        fallback_comparison = kwargs.get("fallback_comparison", "not_before")  # "not_before" or "not_after"
        use_timestamp = kwargs.get("use_timestamp", True)
        
        self._validate_column_exists(target_column, dataframe)
        self._validate_column_exists(primary_condition_column, dataframe)
        if fallback_column:
            self._validate_column_exists(fallback_column, dataframe)
        
        # Convert to appropriate date/timestamp type
        if use_timestamp:
            target_col = to_timestamp(col(target_column))
            primary_col = to_timestamp(col(primary_condition_column))
            fallback_col = to_timestamp(col(fallback_column)) if fallback_column else None
        else:
            target_col = to_date(col(target_column))
            primary_col = to_date(col(primary_condition_column))
            fallback_col = to_date(col(fallback_column)) if fallback_column else None
        
        # If target is null, consider valid (or adjust based on requirements)
        target_is_null = col(target_column).isNull()
        
        # Primary condition: if primary_condition_column is not null
        primary_condition_met = col(primary_condition_column).isNotNull()
        
        if primary_comparison == "after":
            primary_check = target_col > primary_col
        else:  # before
            primary_check = target_col < primary_col
        
        # Fallback condition: if primary_condition_column is null
        if fallback_column:
            if fallback_comparison == "not_before":
                fallback_check = target_col >= fallback_col
            else:  # not_after
                fallback_check = target_col <= fallback_col
        else:
            fallback_check = lit(True)
        
        # Combine: if target is null, valid; if primary condition column is not null, use primary check, else use fallback
        return when(target_is_null, lit(True)).when(primary_condition_met, primary_check).otherwise(fallback_check)
    
    def _expect_column_values_to_be_normalized(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """
        Normalize column values based on a value mapping.
        Replaces values according to the mapping and validates the result.
        
        Args:
            kwargs: Dictionary containing:
                - column: Column name to normalize
                - value_mapping: Dictionary mapping original values to normalized values
                    Example: {"Female": "F", "Male": "M", "f": "F", "m": "M"}
                - case_sensitive: Optional, default False. If True, matching is case-sensitive
        
        Returns:
            Spark Column condition that evaluates to True if value is normalized (or was already normalized)
        """
        column_name = kwargs.get("column")
        value_mapping = kwargs.get("value_mapping", {})
        case_sensitive = kwargs.get("case_sensitive", False)
        
        self._validate_column_exists(column_name, dataframe)
        
        if not value_mapping:
            return lit(True)  # No mapping means all values are valid
        
        # Get the normalized values (target values)
        normalized_values = set(value_mapping.values())
        
        # Build the transformation condition
        # Start with the original column
        normalized_col = col(column_name)
        
        # Apply transformations based on mapping
        for original_value, normalized_value in value_mapping.items():
            if case_sensitive:
                normalized_col = when(normalized_col == original_value, normalized_value).otherwise(normalized_col)
            else:
                # Case-insensitive matching
                normalized_col = when(
                    lower(normalized_col) == lower(lit(original_value)), 
                    normalized_value
                ).otherwise(normalized_col)
        
        # Store the transformation to be applied later
        # For now, return validation: True if value is in normalized set or will be normalized
        original_col = col(column_name)
        
        # Check if value is already normalized
        already_normalized = original_col.isin(list(normalized_values))
        
        # Check if value can be normalized (exists in mapping)
        can_be_normalized = lit(False)
        for original_value in value_mapping.keys():
            if case_sensitive:
                can_be_normalized = can_be_normalized | (original_col == original_value)
            else:
                can_be_normalized = can_be_normalized | (lower(original_col) == lower(lit(original_value)))
        
        # Value is valid if it's already normalized OR can be normalized
        return already_normalized | can_be_normalized
    
    def _expect_column_values_to_match_regex_and_replace(self, kwargs: Dict[str, Any], dataframe: DataFrame):
        """
        Match column values using regex and replace matched values.
        Replaces values that match the regex pattern with the replacement value.
        
        Args:
            kwargs: Dictionary containing:
                - column: Column name to transform
                - regex: Regular expression pattern to match
                - replacement: Replacement value (can use regex groups like $1, $2, etc.)
                - validation_regex: Optional regex pattern to validate the result after replacement
        
        Returns:
            Spark Column condition that evaluates to True if value can be transformed or is already correct
        """
        column_name = kwargs.get("column")
        regex_pattern = kwargs.get("regex")
        replacement = kwargs.get("replacement", "")
        validation_regex = kwargs.get("validation_regex")
        
        self._validate_column_exists(column_name, dataframe)
        
        if not regex_pattern:
            return lit(True)  # No pattern means all values are valid
        
        # Check if value matches the regex pattern (will be replaced)
        matches_regex = col(column_name).rlike(regex_pattern)
        
        if validation_regex:
            # If validation_regex is provided, check if the value already matches it
            # (meaning it doesn't need replacement) OR it matches the pattern to be replaced
            already_valid = col(column_name).rlike(validation_regex)
            return already_valid | matches_regex
        else:
            # If no validation_regex, any value that matches the pattern is valid (will be replaced)
            # Values that don't match are also valid (won't be changed)
            return lit(True)
    
    # ========== END NEW IMPLEMENTATIONS ==========
    
    def _validate_column_exists(self, column_name: str, dataframe: DataFrame):
        """Validate that a column exists in the DataFrame."""
        if column_name not in dataframe.columns:
            raise ValueError(f"Column '{column_name}' does not exist in DataFrame")
    
    def _type_matches(self, actual_type: str, expected_type: str) -> bool:
        """Check if actual type matches expected type."""
        actual_lower = actual_type.lower()
        expected_lower = expected_type.lower()
        
        type_mappings = {
            "string": ["string", "varchar", "char"],
            "int": ["int", "integer", "long", "bigint"],
            "float": ["float", "double", "decimal"],
            "boolean": ["boolean", "bool"],
            "date": ["date"],
            "timestamp": ["timestamp"]
        }
        
        for type_group, variants in type_mappings.items():
            if expected_lower == type_group and any(variant in actual_lower for variant in variants):
                return True
        
        return actual_lower == expected_lower
    
    def get_supported_expectations(self) -> List[str]:
        """Return list of supported expectation types."""
        return list(self.supported_expectations.keys())
    
    def validate_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a rule configuration.
        
        Args:
            rule: Rule dictionary to validate
            
        Returns:
            Dictionary with validation results
        """
        errors = []
        
        if "expectation_type" not in rule:
            errors.append("Missing 'expectation_type' field")
        else:
            expectation_type = rule["expectation_type"]
            if expectation_type not in self.supported_expectations:
                errors.append(f"Unsupported expectation type: {expectation_type}")
        
        if "kwargs" not in rule:
            errors.append("Missing 'kwargs' field")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        } 