# HDF DQ Framework

A powerful Data Quality Framework for PySpark DataFrames using Great Expectations validation rules, designed for the HDF Data Pipeline ecosystem.

**Version: 0.8.0**

## Overview

The DQ Framework provides a simple and efficient way to filter DataFrames based on data quality rules. It separates qualified data from bad data, allowing you to handle data quality issues systematically in your data pipelines.

### Key Features

- **Easy Integration**: Simple API that works with existing PySpark workflows
- **Great Expectations**: Leverages the power of Great Expectations for data validation
- **Flexible Rules**: Support for JSON string, dictionary, or list-based rule configuration
- **Dual Output**: Returns both qualified and bad rows as separate DataFrames
- **Detailed Validation**: Optional validation details for debugging and monitoring
- **Failure Details**: Bad DataFrame automatically includes failure reasons, column names, and failed expectations
- **Warning vs Error**: Support for `isWarning` flag to distinguish between warnings and errors in validation rules

## Changelog

### Version 0.8.0 (Current)

#### New Features

- **isWarning Flag Support**: Added support for `isWarning` flag in rule configuration to distinguish between warnings and errors

  - Rules can now include `"isWarning": true` to mark validation failures as warnings instead of errors
  - Bad DataFrame includes `_dq_is_warning` column indicating if any failed rule is a warning
  - Useful for data quality monitoring where some issues are informational rather than blocking

- **Enhanced Failure Details**: Bad DataFrame now includes comprehensive failure information:
  - `_dq_failed_expectations`: List of failed expectation types (pipe-separated)
  - `_dq_failed_columns`: List of columns involved in failures (pipe-separated)
  - `_dq_failure_reasons`: Human-readable reasons for each failure (pipe-separated)
  - `_dq_is_warning`: Boolean flag indicating if any failed rule is marked as a warning

#### New Expectation Types

Added support for advanced date and conditional validation rules:

- `expect_column_values_to_not_be_future_date`: Validates dates are not in the future
- `expect_column_values_to_not_be_older_than_years`: Validates dates are not older than specified years
- `expect_column_values_to_be_after_column`: Validates column A is after column B (for dates/timestamps)
- `expect_column_values_to_be_after_column_if_populated`: Conditional date comparison when column is populated
- `expect_column_values_to_not_be_before_column_if_populated`: Conditional date validation when column is populated
- `expect_column_to_not_be_null_if_condition`: Validates target column is not null when condition is met
- `expect_column_values_conditional_date_comparison`: Complex conditional date comparisons with fallback logic

#### Improvements

- Enhanced failure reason generation with more descriptive, human-readable messages
- Better column extraction from rule configurations for improved failure reporting
- Improved documentation with examples for all new expectation types

### Version 0.5.0

- Initial release with core data quality validation features
- Support for basic Great Expectations expectation types
- DataFrame filtering and validation capabilities

## Quick Start

```python
from pyspark.sql import SparkSession
from dq_framework import DQFramework

# Initialize Spark session
spark = SparkSession.builder.appName("DQ_Example").getOrCreate()

# Create sample data
data = [
    (1, "John", 25, "john@email.com"),
    (2, "Jane", -5, "invalid-email"),  # Bad data: negative age, invalid email
    (3, "Bob", 30, "bob@email.com"),
    (4, None, 35, "alice@email.com"),  # Bad data: null name
]
columns = ["id", "name", "age", "email"]
df = spark.createDataFrame(data, columns)

# Define quality rules
quality_rules = [
    {
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "name"}
    },
    {
        "expectation_type": "expect_column_values_to_be_between",
        "kwargs": {"column": "age", "min_value": 0, "max_value": 120}
    },
    {
        "expectation_type": "expect_column_values_to_match_regex",
        "kwargs": {"column": "email", "regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"}
    }
]

# Initialize DQ Framework
dq = DQFramework()

# Filter data
qualified_df, bad_df = dq.filter_dataframe(
    dataframe=df,
    quality_rules=quality_rules,
    include_validation_details=True
)

# Show results
print("Qualified Data:")
qualified_df.show()

print("Bad Data:")
bad_df.show()

# Bad DataFrame includes failure details:
# - _dq_failed_expectations: Which rules failed
# - _dq_failed_columns: Which columns were involved
# - _dq_failure_reasons: Human-readable reasons for failures
```

## API Reference

### DQFramework

The main class for data quality processing.

#### Methods

- **`filter_dataframe(dataframe, quality_rules, columns=None, include_validation_details=False)`**
  - Filters a DataFrame based on quality rules
  - Returns tuple of (qualified_df, bad_df)
  - Bad DataFrame automatically includes failure details:
    - `_dq_failed_expectations`: List of failed expectation types (pipe-separated)
    - `_dq_failed_columns`: List of columns involved in failures (pipe-separated)
    - `_dq_failure_reasons`: Human-readable reasons for each failure (pipe-separated)
    - `_dq_is_warning`: Boolean flag indicating if any failed rule is marked as a warning (True if any failed rule has `isWarning: true`)

### RuleProcessor

Handles the processing of Great Expectations rules.

## Dependencies

### Core Dependencies

- **PySpark** ^3.0.0: For DataFrame operations
- **Great Expectations** ^0.15.0: For validation logic
- **typing-extensions** ^4.0.0: For enhanced type hints

## Supported Expectations

The DQ Framework supports a comprehensive set of Great Expectations validation rules. Below are all available expectations organized by category, with examples and descriptions.

### 1. Basic Column Existence and Null Checks

#### `expect_column_to_exist`

Validates that a specified column exists in the DataFrame.

```python
{
    "expectation_type": "expect_column_to_exist",
    "kwargs": {"column": "customer_id"}
}
```

#### `expect_column_values_to_not_be_null`

Validates that column values are not null.

```python
{
    "expectation_type": "expect_column_values_to_not_be_null",
    "kwargs": {"column": "email"}
}
```

#### `expect_column_values_to_be_null`

Validates that column values are null (useful for optional fields in specific contexts).

```python
{
    "expectation_type": "expect_column_values_to_be_null",
    "kwargs": {"column": "middle_name"}
}
```

### 2. Uniqueness Expectations

#### `expect_column_values_to_be_unique`

Validates that all values in a column are unique.

```python
{
    "expectation_type": "expect_column_values_to_be_unique",
    "kwargs": {"column": "user_id"}
}
```

#### `expect_compound_columns_to_be_unique`

Validates that combinations of multiple column values are unique.

```python
{
    "expectation_type": "expect_compound_columns_to_be_unique",
    "kwargs": {"column_list": ["user_id", "transaction_date", "amount"]}
}
```

#### `expect_select_column_values_to_be_unique_within_record`

Validates that values are unique within each record across specified columns.

```python
{
    "expectation_type": "expect_select_column_values_to_be_unique_within_record",
    "kwargs": {"column_list": ["phone_home", "phone_work", "phone_mobile"]}
}
```

#### `expect_multicolumn_values_to_be_unique`

Validates that combinations of multiple column values are unique (alias for compound_columns).

```python
{
    "expectation_type": "expect_multicolumn_values_to_be_unique",
    "kwargs": {"column_list": ["order_id", "product_id"]}
}
```

### 3. Range and Value Expectations

#### `expect_column_values_to_be_between`

Validates that column values are within a specified numeric range.

```python
{
    "expectation_type": "expect_column_values_to_be_between",
    "kwargs": {"column": "age", "min_value": 0, "max_value": 120}
}

# Age must be between 18 and 65
{
    "expectation_type": "expect_column_values_to_be_between",
    "kwargs": {"column": "age", "min_value": 18, "max_value": 65}
}

# Price must be at least 0 (no maximum)
{
    "expectation_type": "expect_column_values_to_be_between",
    "kwargs": {"column": "price", "min_value": 0}
}
```

#### `expect_column_values_to_be_in_set`

Validates that column values are within a specified set of allowed values.

```python
{
    "expectation_type": "expect_column_values_to_be_in_set",
    "kwargs": {
        "column": "status",
        "value_set": ["active", "inactive", "suspended", "pending"]
    }
}

# Gender validation
{
    "expectation_type": "expect_column_values_to_be_in_set",
    "kwargs": {
        "column": "gender",
        "value_set": ["M", "F", "Other", "Prefer not to say"]
    }
}
```

#### `expect_column_values_to_not_be_in_set`

Validates that column values are NOT in a specified set of disallowed values.

```python
{
    "expectation_type": "expect_column_values_to_not_be_in_set",
    "kwargs": {
        "column": "username",
        "value_set": ["admin", "root", "test", "guest"]
    }
}
```

#### `expect_column_distinct_values_to_be_in_set`

Validates that all distinct values in a column are within a specified set.

```python
{
    "expectation_type": "expect_column_distinct_values_to_be_in_set",
    "kwargs": {
        "column": "department",
        "value_set": ["HR", "Finance", "Engineering", "Marketing", "Sales"]
    }
}
```

#### `expect_column_distinct_values_to_contain_set`

Validates that the column contains all values from a specified set.

```python
{
    "expectation_type": "expect_column_distinct_values_to_contain_set",
    "kwargs": {
        "column": "required_skills",
        "value_set": ["Python", "SQL"]
    }
}
```

#### `expect_column_distinct_values_to_equal_set`

Validates that distinct values in a column exactly match a specified set.

```python
{
    "expectation_type": "expect_column_distinct_values_to_equal_set",
    "kwargs": {
        "column": "grade",
        "value_set": ["A", "B", "C", "D", "F"]
    }
}
```

### 4. Pattern Matching Expectations

#### `expect_column_values_to_match_regex`

Validates that column values match a specified regular expression pattern.

```python
# Email validation
{
    "expectation_type": "expect_column_values_to_match_regex",
    "kwargs": {
        "column": "email",
        "regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    }
}

# Phone number validation (US format)
{
    "expectation_type": "expect_column_values_to_match_regex",
    "kwargs": {
        "column": "phone",
        "regex": r"^\(\d{3}\) \d{3}-\d{4}$"
    }
}

# Product code validation (3 letters + 4 digits)
{
    "expectation_type": "expect_column_values_to_match_regex",
    "kwargs": {
        "column": "product_code",
        "regex": r"^[A-Z]{3}\d{4}$"
    }
}
```

#### `expect_column_values_to_not_match_regex`

Validates that column values do NOT match a specified regular expression pattern.

```python
# Ensure no special characters in username
{
    "expectation_type": "expect_column_values_to_not_match_regex",
    "kwargs": {
        "column": "username",
        "regex": r"[!@#$%^&*()+=\[\]{};':\"\\|,.<>/?]"
    }
}
```

#### `expect_column_values_to_match_strftime_format`

Validates that column values match a specific date/time format.

```python
# Date in YYYY-MM-DD format
{
    "expectation_type": "expect_column_values_to_match_strftime_format",
    "kwargs": {
        "column": "birth_date",
        "strftime_format": "%Y-%m-%d"
    }
}

# Timestamp in YYYY-MM-DD HH:MM:SS format
{
    "expectation_type": "expect_column_values_to_match_strftime_format",
    "kwargs": {
        "column": "created_at",
        "strftime_format": "%Y-%m-%d %H:%M:%S"
    }
}
```

### 5. String Length Expectations

#### `expect_column_value_lengths_to_be_between`

Validates that string column value lengths are within a specified range.

```python
# Password length validation
{
    "expectation_type": "expect_column_value_lengths_to_be_between",
    "kwargs": {"column": "password", "min_value": 8, "max_value": 128}
}

# Comment length validation
{
    "expectation_type": "expect_column_value_lengths_to_be_between",
    "kwargs": {"column": "comment", "min_value": 1, "max_value": 500}
}
```

#### `expect_column_value_lengths_to_equal`

Validates that string column value lengths equal a specific value.

```python
# Country code (ISO 3166-1 alpha-2)
{
    "expectation_type": "expect_column_value_lengths_to_equal",
    "kwargs": {"column": "country_code", "value": 2}
}

# SSN format (XXX-XX-XXXX = 11 characters)
{
    "expectation_type": "expect_column_value_lengths_to_equal",
    "kwargs": {"column": "ssn", "value": 11}
}
```

### 6. Type Expectations

#### `expect_column_values_to_be_of_type`

Validates that column values are of a specified data type.

```python
{
    "expectation_type": "expect_column_values_to_be_of_type",
    "kwargs": {"column": "age", "type_": "int"}
}

{
    "expectation_type": "expect_column_values_to_be_of_type",
    "kwargs": {"column": "price", "type_": "float"}
}

{
    "expectation_type": "expect_column_values_to_be_of_type",
    "kwargs": {"column": "name", "type_": "string"}
}
```

#### `expect_column_values_to_be_in_type_list`

Validates that column values are of one of the specified data types.

```python
{
    "expectation_type": "expect_column_values_to_be_in_type_list",
    "kwargs": {
        "column": "numeric_value",
        "type_list": ["int", "float", "double"]
    }
}
```

### 7. Date and Time Expectations

#### `expect_column_values_to_be_dateutil_parseable`

Validates that column values can be parsed as valid dates.

```python
{
    "expectation_type": "expect_column_values_to_be_dateutil_parseable",
    "kwargs": {"column": "event_date"}
}
```

#### `expect_column_values_to_not_be_future_date`

Validates that column values are not future dates.

```python
# Date column should not be in the future
{
    "expectation_type": "expect_column_values_to_not_be_future_date",
    "kwargs": {"column": "birth_date"}
}

# Timestamp column should not be in the future (as a warning, not an error)
{
    "expectation_type": "expect_column_values_to_not_be_future_date",
    "kwargs": {"column": "created_timestamp", "use_timestamp": True},
    "isWarning": True  # Mark this as a warning instead of an error
}
```

#### `expect_column_values_to_not_be_older_than_years`

Validates that column values are not older than a specified number of years.

```python
# Date should not be older than 150 years
{
    "expectation_type": "expect_column_values_to_not_be_older_than_years",
    "kwargs": {"column": "birth_date", "years": 150}
}

# Timestamp should not be older than 10 years
{
    "expectation_type": "expect_column_values_to_not_be_older_than_years",
    "kwargs": {"column": "created_timestamp", "years": 10, "use_timestamp": True}
}
```

### 7a. Advanced Date and Conditional Column Expectations

#### `expect_column_values_to_be_after_column`

Validates that values in column A are after values in column B (for dates/timestamps).

```python
# End date must be after start date
{
    "expectation_type": "expect_column_values_to_be_after_column",
    "kwargs": {"column_A": "end_date", "column_B": "start_date", "use_timestamp": False}
}

# End timestamp must be after or equal to start timestamp
{
    "expectation_type": "expect_column_values_to_be_after_column",
    "kwargs": {"column_A": "end_datetime", "column_B": "start_datetime", "or_equal": True, "use_timestamp": True}
}
```

#### `expect_column_values_to_be_after_column_if_populated`

Validates that if column A is populated (not null), it should be after column B.

```python
# If populated, should be after CreatedDateTime
{
    "expectation_type": "expect_column_values_to_be_after_column_if_populated",
    "kwargs": {"column_A": "updated_date", "column_B": "created_date", "use_timestamp": False}
}
```

#### `expect_column_values_to_not_be_before_column_if_populated`

Validates that if column A is populated (not null), it should not be before column B.

```python
# If populated, should not be before UpdatedDateTime
{
    "expectation_type": "expect_column_values_to_not_be_before_column_if_populated",
    "kwargs": {"column_A": "some_date", "column_B": "updated_datetime", "use_timestamp": True}
}
```

#### `expect_column_to_not_be_null_if_condition`

Validates that if a condition column is True (or a specific value), then the target column should not be null.

```python
# If IsPatientMerged is True, then MergedPatientId should not be null
{
    "expectation_type": "expect_column_to_not_be_null_if_condition",
    "kwargs": {
        "condition_column": "IsPatientMerged",
        "target_column": "MergedPatientId",
        "condition_value": True
    },
    "isWarning": False  # This is an error (default behavior)
}
```

**Note:** The `isWarning` flag is optional and defaults to `False`. When set to `True`, failed rows will have `_dq_is_warning` set to `True` in the bad DataFrame, allowing you to distinguish between warnings and errors.

#### `expect_column_values_conditional_date_comparison`

Validates complex conditional date comparisons with fallback logic.

```python
# DeceasedDatetime must be after DateOfBirth if DateOfBirth is not null,
# else DeceasedDatetime should not be before CreatedDateTime
{
    "expectation_type": "expect_column_values_conditional_date_comparison",
    "kwargs": {
        "target_column": "DeceasedDatetime",
        "primary_condition_column": "DateOfBirth",
        "primary_comparison": "after",
        "fallback_column": "CreatedDateTime",
        "fallback_comparison": "not_before",
        "use_timestamp": True
    }
}
```

### 8. JSON Expectations

#### `expect_column_values_to_be_json_parseable`

Validates that column values are valid JSON strings.

```python
{
    "expectation_type": "expect_column_values_to_be_json_parseable",
    "kwargs": {"column": "metadata"}
}
```

#### `expect_column_values_to_match_json_schema`

Validates that column values match a specified JSON schema.

```python
{
    "expectation_type": "expect_column_values_to_match_json_schema",
    "kwargs": {
        "column": "user_preferences",
        "json_schema": {
            "type": "object",
            "properties": {
                "theme": {"type": "string"},
                "notifications": {"type": "boolean"}
            }
        }
    }
}
```

### 9. Ordering Expectations

#### `expect_column_values_to_be_increasing`

Validates that column values are in increasing order.

```python
# Values must be increasing (non-strict)
{
    "expectation_type": "expect_column_values_to_be_increasing",
    "kwargs": {"column": "timestamp"}
}

# Values must be strictly increasing
{
    "expectation_type": "expect_column_values_to_be_increasing",
    "kwargs": {"column": "sequence_number", "strictly": True}
}
```

#### `expect_column_values_to_be_decreasing`

Validates that column values are in decreasing order.

```python
# Values must be decreasing (non-strict)
{
    "expectation_type": "expect_column_values_to_be_decreasing",
    "kwargs": {"column": "priority_score"}
}

# Values must be strictly decreasing
{
    "expectation_type": "expect_column_values_to_be_decreasing",
    "kwargs": {"column": "countdown", "strictly": True}
}
```

### 10. Statistical Expectations

#### `expect_column_mean_to_be_between`

Validates that the column mean is within a specified range.

```python
{
    "expectation_type": "expect_column_mean_to_be_between",
    "kwargs": {"column": "test_scores", "min_value": 70, "max_value": 90}
}
```

#### `expect_column_median_to_be_between`

Validates that the column median is within a specified range.

```python
{
    "expectation_type": "expect_column_median_to_be_between",
    "kwargs": {"column": "response_time", "min_value": 100, "max_value": 500}
}
```

#### `expect_column_stdev_to_be_between`

Validates that the column standard deviation is within a specified range.

```python
{
    "expectation_type": "expect_column_stdev_to_be_between",
    "kwargs": {"column": "measurements", "min_value": 0.5, "max_value": 2.0}
}
```

#### `expect_column_unique_value_count_to_be_between`

Validates that the count of unique values is within a specified range.

```python
{
    "expectation_type": "expect_column_unique_value_count_to_be_between",
    "kwargs": {"column": "category", "min_value": 5, "max_value": 20}
}
```

#### `expect_column_proportion_of_unique_values_to_be_between`

Validates that the proportion of unique values is within a specified range.

```python
{
    "expectation_type": "expect_column_proportion_of_unique_values_to_be_between",
    "kwargs": {"column": "user_id", "min_value": 0.95, "max_value": 1.0}
}
```

#### `expect_column_most_common_value_to_be_in_set`

Validates that the most common value is within a specified set.

```python
{
    "expectation_type": "expect_column_most_common_value_to_be_in_set",
    "kwargs": {
        "column": "preferred_language",
        "value_set": ["English", "Spanish", "French"]
    }
}
```

#### `expect_column_max_to_be_between`

Validates that the column maximum value is within a specified range.

```python
{
    "expectation_type": "expect_column_max_to_be_between",
    "kwargs": {"column": "temperature", "min_value": -50, "max_value": 50}
}
```

#### `expect_column_min_to_be_between`

Validates that the column minimum value is within a specified range.

```python
{
    "expectation_type": "expect_column_min_to_be_between",
    "kwargs": {"column": "price", "min_value": 0, "max_value": 10}
}
```

#### `expect_column_sum_to_be_between`

Validates that the column sum is within a specified range.

```python
{
    "expectation_type": "expect_column_sum_to_be_between",
    "kwargs": {"column": "order_amount", "min_value": 1000, "max_value": 100000}
}
```

#### `expect_column_quantile_values_to_be_between`

Validates that column quantile values are within specified ranges.

```python
{
    "expectation_type": "expect_column_quantile_values_to_be_between",
    "kwargs": {
        "column": "response_time",
        "quantile_ranges": {
            "quantiles": [0.25, 0.5, 0.75],
            "value_ranges": [[50, 100], [100, 200], [200, 400]]
        }
    }
}
```

### 11. Column Pair Expectations

#### `expect_column_pair_values_to_be_equal`

Validates that values in two columns are equal.

```python
{
    "expectation_type": "expect_column_pair_values_to_be_equal",
    "kwargs": {"column_A": "password", "column_B": "password_confirm"}
}
```

#### `expect_column_pair_values_A_to_be_greater_than_B`

Validates that values in column A are greater than values in column B.

```python
# End date must be after start date
{
    "expectation_type": "expect_column_pair_values_A_to_be_greater_than_B",
    "kwargs": {"column_A": "end_date", "column_B": "start_date"}
}

# Final score must be greater than or equal to initial score
{
    "expectation_type": "expect_column_pair_values_A_to_be_greater_than_B",
    "kwargs": {"column_A": "final_score", "column_B": "initial_score", "or_equal": True}
}
```

#### `expect_column_pair_values_to_be_in_set`

Validates that pairs of values are within a specified set of valid combinations.

```python
{
    "expectation_type": "expect_column_pair_values_to_be_in_set",
    "kwargs": {
        "column_A": "state",
        "column_B": "country",
        "value_pairs_set": [
            ["CA", "USA"],
            ["NY", "USA"],
            ["TX", "USA"],
            ["ON", "Canada"],
            ["BC", "Canada"]
        ]
    }
}
```

### 12. Table-level Expectations

#### `expect_table_row_count_to_be_between`

Validates that the total number of rows in the table is within a specified range.

```python
{
    "expectation_type": "expect_table_row_count_to_be_between",
    "kwargs": {"min_value": 100, "max_value": 10000}
}
```

#### `expect_table_row_count_to_equal`

Validates that the total number of rows equals a specific value.

```python
{
    "expectation_type": "expect_table_row_count_to_equal",
    "kwargs": {"value": 1000}
}
```

#### `expect_table_column_count_to_be_between`

Validates that the number of columns is within a specified range.

```python
{
    "expectation_type": "expect_table_column_count_to_be_between",
    "kwargs": {"min_value": 5, "max_value": 50}
}
```

#### `expect_table_column_count_to_equal`

Validates that the number of columns equals a specific value.

```python
{
    "expectation_type": "expect_table_column_count_to_equal",
    "kwargs": {"value": 12}
}
```

#### `expect_table_columns_to_match_ordered_list`

Validates that table columns match an ordered list exactly.

```python
{
    "expectation_type": "expect_table_columns_to_match_ordered_list",
    "kwargs": {
        "column_list": ["id", "name", "email", "created_at", "updated_at"]
    }
}
```

#### `expect_table_columns_to_match_set`

Validates that table columns match a set (order doesn't matter).

```python
{
    "expectation_type": "expect_table_columns_to_match_set",
    "kwargs": {
        "column_set": ["user_id", "product_id", "quantity", "price", "order_date"]
    }
}
```

## Complete Example: E-commerce Order Validation

Here's a comprehensive example showing multiple expectations for validating e-commerce order data:

```python
from pyspark.sql import SparkSession
from dq_framework import DQFramework

# Initialize Spark session
spark = SparkSession.builder.appName("ECommerce_DQ").getOrCreate()

# Sample e-commerce order data
data = [
    (1, "ORD001", "user123", "PROD-A001", 2, 29.99, "2023-01-15", "completed"),
    (2, "ORD002", "user456", "PROD-B002", 1, 15.50, "2023-01-16", "pending"),
    (3, "ORD003", "user789", "PROD-C003", 0, 45.00, "2023-01-17", "cancelled"),  # Bad: quantity = 0
    (4, "ORD004", "", "PROD-D004", 1, -10.00, "2023-01-18", "processing"),      # Bad: empty user_id, negative price
    (5, "ORD005", "user123", "INVALID", 3, 75.25, "invalid-date", "unknown")    # Bad: invalid product code, date, status
]

columns = ["id", "order_id", "user_id", "product_code", "quantity", "price", "order_date", "status"]
df = spark.createDataFrame(data, columns)

# Comprehensive quality rules
quality_rules = [
    # Basic existence and null checks
    {
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "order_id"}
    },
    {
        "expectation_type": "expect_column_values_to_not_be_null",
        "kwargs": {"column": "user_id"}
    },

    # Uniqueness
    {
        "expectation_type": "expect_column_values_to_be_unique",
        "kwargs": {"column": "order_id"}
    },

    # Range validation
    {
        "expectation_type": "expect_column_values_to_be_between",
        "kwargs": {"column": "quantity", "min_value": 1, "max_value": 100}
    },
    {
        "expectation_type": "expect_column_values_to_be_between",
        "kwargs": {"column": "price", "min_value": 0.01, "max_value": 10000}
    },

    # Set validation
    {
        "expectation_type": "expect_column_values_to_be_in_set",
        "kwargs": {
            "column": "status",
            "value_set": ["pending", "processing", "completed", "cancelled"]
        }
    },

    # Pattern matching
    {
        "expectation_type": "expect_column_values_to_match_regex",
        "kwargs": {
            "column": "product_code",
            "regex": r"^PROD-[A-Z]\d{3}$"
        }
    },
    {
        "expectation_type": "expect_column_values_to_match_strftime_format",
        "kwargs": {
            "column": "order_date",
            "strftime_format": "%Y-%m-%d"
        }
    },

    # String length
    {
        "expectation_type": "expect_column_value_lengths_to_be_between",
        "kwargs": {"column": "user_id", "min_value": 3, "max_value": 20}
    }
]

# Initialize DQ Framework and filter data
dq = DQFramework()
qualified_df, bad_df = dq.filter_dataframe(
    dataframe=df,
    quality_rules=quality_rules,
    include_validation_details=True
)

print("Qualified Orders:")
qualified_df.show()

print("Bad Orders:")
bad_df.show()
```

This example demonstrates how multiple expectations work together to ensure comprehensive data quality validation for real-world scenarios.

## Advanced Example: Healthcare Patient Data Validation

Here's a comprehensive example demonstrating the new advanced date and conditional validation rules for healthcare patient data:

```python
from pyspark.sql import SparkSession
from dq_framework import DQFramework

# Initialize Spark session
spark = SparkSession.builder.appName("Healthcare_DQ").getOrCreate()

# Sample healthcare patient data
data = [
    (1, "2023-01-15", "2023-01-20", "1990-05-10", "2023-12-01", True, "P12345", "2023-01-10"),
    (2, "2024-01-15", "2024-01-20", "1850-01-01", None, False, None, "2023-01-10"),  # Bad: future date, too old
    (3, "2023-01-15", "2023-01-10", "1995-06-15", None, True, None, "2023-01-10"),  # Bad: before created, merged without ID
    (4, "2023-01-15", "2023-01-20", None, "2023-12-01", False, None, "2023-01-10"),  # Valid
    (5, "2023-01-15", "2023-01-20", "2000-01-01", "1999-12-31", False, None, "2023-01-10"),  # Bad: deceased before birth
]

columns = [
    "id", "CreatedDateTime", "UpdatedDateTime", "DateOfBirth",
    "DeceasedDatetime", "IsPatientMerged", "MergedPatientId", "AdmissionDateTime"
]
df = spark.createDataFrame(data, columns)

# Advanced quality rules covering all the new validation types
quality_rules = [
    # Should not be a future date
    {
        "expectation_type": "expect_column_values_to_not_be_future_date",
        "kwargs": {"column": "CreatedDateTime", "use_timestamp": False}
    },

    # Should not be older than 150 years
    {
        "expectation_type": "expect_column_values_to_not_be_older_than_years",
        "kwargs": {"column": "DateOfBirth", "years": 150, "use_timestamp": False}
    },

    # If populated, should not be before UpdatedDateTime
    {
        "expectation_type": "expect_column_values_to_not_be_before_column_if_populated",
        "kwargs": {
            "column_A": "CreatedDateTime",
            "column_B": "UpdatedDateTime",
            "use_timestamp": False
        }
    },

    # If populated, should be after CreatedDateTime
    {
        "expectation_type": "expect_column_values_to_be_after_column_if_populated",
        "kwargs": {
            "column_A": "UpdatedDateTime",
            "column_B": "CreatedDateTime",
            "use_timestamp": False
        }
    },

    # DeceasedDatetime must be after DateOfBirth if DateOfBirth is not null,
    # else DeceasedDatetime should not be before CreatedDateTime
    {
        "expectation_type": "expect_column_values_conditional_date_comparison",
        "kwargs": {
            "target_column": "DeceasedDatetime",
            "primary_condition_column": "DateOfBirth",
            "primary_comparison": "after",
            "fallback_column": "CreatedDateTime",
            "fallback_comparison": "not_before",
            "use_timestamp": False
        }
    },

    # If IsPatientMerged is True then MergedPatientId should not be null
    {
        "expectation_type": "expect_column_to_not_be_null_if_condition",
        "kwargs": {
            "condition_column": "IsPatientMerged",
            "target_column": "MergedPatientId",
            "condition_value": True
        }
    },

    # Must be after startdatetime (using AdmissionDateTime as example)
    {
        "expectation_type": "expect_column_values_to_be_after_column",
        "kwargs": {
            "column_A": "UpdatedDateTime",
            "column_B": "AdmissionDateTime",
            "use_timestamp": False
        }
    },

    # Must be after admissiondatetime
    {
        "expectation_type": "expect_column_values_to_be_after_column",
        "kwargs": {
            "column_A": "CreatedDateTime",
            "column_B": "AdmissionDateTime",
            "use_timestamp": False
        }
    }
]

# Initialize DQ Framework and filter data
dq = DQFramework()
qualified_df, bad_df = dq.filter_dataframe(
    dataframe=df,
    quality_rules=quality_rules,
    include_validation_details=True
)

print("Qualified Patient Records:")
qualified_df.show()

print("Bad Patient Records:")
bad_df.show()
```

This example demonstrates all the advanced validation rules:

- **Future date validation**: Ensures dates are not in the future
- **Age validation**: Ensures dates are not older than 150 years
- **Conditional column comparisons**: Validates relationships between columns when values are populated
- **Complex conditional logic**: Handles multi-condition date comparisons with fallback logic
- **Conditional null checks**: Ensures required fields are populated based on conditions
