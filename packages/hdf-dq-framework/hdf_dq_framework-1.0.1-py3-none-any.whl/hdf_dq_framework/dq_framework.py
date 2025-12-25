import json
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, when, lit, coalesce, array, array_union, array_join
from pyspark.sql.types import BooleanType, StringType, ArrayType
try:
    from .rule_processor import RuleProcessor
except ImportError:
    from rule_processor import RuleProcessor


class DQFramework:
    """
    Data Quality Framework that filters DataFrames based on Great Expectations rules.
    
    Takes quality rules, columns, and a DataFrame as input.
    Returns qualified rows and bad rows as separate DataFrames.
    """
    
    def __init__(self):
        """
        Initialize the DQ Framework.
        """
        self.rule_processor = RuleProcessor()
    
    def filter_dataframe(
        self,
        dataframe: DataFrame,
        quality_rules: Union[str, Dict, List[Dict]],
        columns: Optional[List[str]] = None,
        include_validation_details: bool = False
    ) -> Tuple[DataFrame, DataFrame]:
        """
        Filter a DataFrame based on quality rules, returning qualified and bad rows.
        
        Args:
            dataframe: The Spark DataFrame to filter
            quality_rules: Quality rules as JSON string, dict, or list of expectations
            columns: Optional list of columns to focus validation on. If None, uses all columns
            include_validation_details: If True, adds validation detail columns to output
            
        Returns:
            Tuple of (qualified_df, bad_df) - DataFrames with qualified and bad rows
        """
        # Parse quality rules
        parsed_rules = self._parse_quality_rules(quality_rules)
        self._parsed_rules = parsed_rules  # Store for failure reporting
        
        # Filter columns if specified
        if columns:
            dataframe = dataframe.select(*columns)
        
        # Create row-level validation flags
        validation_df = self._create_validation_flags(dataframe, parsed_rules)
        
        # Split into qualified and bad rows
        qualified_df, bad_df = self._split_dataframe(
            validation_df, 
            include_validation_details
        )
        
        return qualified_df, bad_df
    
    def validate_and_filter(
        self,
        dataframe: DataFrame,
        quality_rules: Union[str, Dict, List[Dict]],
        columns: Optional[List[str]] = None,
        return_validation_summary: bool = True
    ) -> Dict[str, Any]:
        """
        Validate and filter a DataFrame, returning detailed results.
        
        Args:
            dataframe: The Spark DataFrame to validate and filter
            quality_rules: Quality rules as JSON string, dict, or list of expectations
            columns: Optional list of columns to focus validation on
            return_validation_summary: If True, includes detailed validation summary
            
        Returns:
            Dictionary containing qualified_df, bad_df, and optional validation summary
        """
        qualified_df, bad_df = self.filter_dataframe(
            dataframe, quality_rules, columns, include_validation_details=True
        )
        
        result = {
            "qualified_df": qualified_df,
            "bad_df": bad_df,
            "qualified_count": qualified_df.count(),
            "bad_count": bad_df.count(),
            "total_count": dataframe.count()
        }
        
        if return_validation_summary:
            result["validation_summary"] = self._create_validation_summary(
                dataframe, qualified_df, bad_df, quality_rules
            )
        
        return result
    
    def _parse_quality_rules(self, quality_rules: Union[str, Dict, List[Dict]]) -> List[Dict]:
        """Parse quality rules into a standardized list format."""
        if isinstance(quality_rules, str):
            quality_rules = json.loads(quality_rules)
        
        if isinstance(quality_rules, dict):
            if "expectations" in quality_rules:
                return quality_rules["expectations"]
            else:
                return [quality_rules]
        
        return quality_rules
    
    def _create_validation_flags(self, dataframe: DataFrame, rules: List[Dict]) -> DataFrame:
        """Create boolean validation flags for each rule and combine them."""
        validation_df = dataframe
        rule_columns = []
        rule_metadata = []  # Store rule metadata for failure reporting
        
        for i, rule in enumerate(rules):
            rule_name = f"rule_{i}_{rule.get('expectation_type', 'unknown')}"
            rule_columns.append(rule_name)
            
            # Extract rule metadata
            expectation_type = rule.get('expectation_type', 'unknown')
            columns_involved = self._extract_columns_from_rule(rule)
            is_warning = rule.get('isWarning', False)  # Extract isWarning flag
            rule_metadata.append({
                'rule_name': rule_name,
                'expectation_type': expectation_type,
                'columns': columns_involved,
                'rule_index': i,
                'is_warning': is_warning
            })
            
            # Check if this is a transformation expectation and apply transformation first
            if self.rule_processor.is_transformation_expectation(expectation_type):
                transformation_col = self.rule_processor.create_transformation_column(rule, validation_df)
                if transformation_col is not None:
                    column_name = rule.get('kwargs', {}).get('column')
                    if column_name:
                        # Apply the transformation to the column
                        validation_df = validation_df.withColumn(column_name, transformation_col)
            
            # Create validation condition for this rule
            condition = self.rule_processor.create_validation_condition(rule, validation_df)
            validation_df = validation_df.withColumn(rule_name, condition)
        
        # Create overall validation flag (all rules must pass)
        if rule_columns:
            overall_condition = col(rule_columns[0])
            for rule_col in rule_columns[1:]:
                overall_condition = overall_condition & col(rule_col)
            
            validation_df = validation_df.withColumn("_dq_is_valid", overall_condition)
        else:
            # No rules means all rows are valid
            validation_df = validation_df.withColumn("_dq_is_valid", lit(True))
        
        # Store rule metadata for later use in failure reporting
        self._rule_metadata = rule_metadata
        self._rule_columns = rule_columns
        
        return validation_df
    
    def _split_dataframe(
        self, 
        validation_df: DataFrame, 
        include_validation_details: bool
    ) -> Tuple[DataFrame, DataFrame]:
        """Split the dataframe into qualified and bad rows based on validation flags."""
        
        # Get original columns (exclude our DQ columns and rule columns)
        original_columns = [col_name for col_name in validation_df.columns 
                          if not col_name.startswith("_dq_") and not col_name.startswith("rule_")]
        
        # Filter qualified and bad rows
        qualified_df = validation_df.filter(col("_dq_is_valid") == True)
        bad_df = validation_df.filter(col("_dq_is_valid") == False)
        
        # Add failure details to bad_df (including isWarning flag)
        if bad_df.count() > 0 and hasattr(self, '_rule_metadata') and self._rule_metadata:
            bad_df = self._add_failure_details(bad_df)
        
        # Always exclude rule columns and _dq_is_valid from output
        # For qualified_df: only original columns (explicitly filter out rule_ and _dq_is_valid)
        qualified_columns = [c for c in qualified_df.columns 
                            if not c.startswith("rule_") and c != "_dq_is_valid"]
        qualified_df = qualified_df.select(*qualified_columns)
        
        # For bad_df: original columns + failure detail columns (rule columns already removed by _add_failure_details)
        # Explicitly filter out any remaining rule_ columns and _dq_is_valid
        bad_columns_to_keep = [c for c in bad_df.columns 
                              if not c.startswith("rule_") and c != "_dq_is_valid"]
        bad_df = bad_df.select(*bad_columns_to_keep)
        
        return qualified_df, bad_df
    
    def _extract_columns_from_rule(self, rule: Dict[str, Any]) -> List[str]:
        """Extract column names from a rule's kwargs."""
        kwargs = rule.get('kwargs', {})
        columns = []
        
        # Common column parameter names
        column_params = ['column', 'column_A', 'column_B', 'target_column', 
                        'condition_column', 'primary_condition_column', 'fallback_column']
        
        for param in column_params:
            if param in kwargs:
                col_name = kwargs[param]
                if col_name and col_name not in columns:
                    columns.append(col_name)
        
        # Handle column_list
        if 'column_list' in kwargs:
            col_list = kwargs['column_list']
            if isinstance(col_list, list):
                columns.extend([c for c in col_list if c and c not in columns])
        
        # Handle column_set
        if 'column_set' in kwargs:
            col_set = kwargs['column_set']
            if isinstance(col_set, list):
                columns.extend([c for c in col_set if c and c not in columns])
        
        return columns
    
    def _generate_failure_reason(self, rule: Dict[str, Any], columns: List[str]) -> str:
        """Generate a human-readable failure reason for a rule."""
        expectation_type = rule.get('expectation_type', 'unknown')
        kwargs = rule.get('kwargs', {})
        
        # Map expectation types to readable messages
        reason_templates = {
            'expect_column_values_to_not_be_null': f"Column '{columns[0] if columns else 'unknown'}' contains null values",
            'expect_column_values_to_be_null': f"Column '{columns[0] if columns else 'unknown'}' should be null but contains values",
            'expect_column_values_to_be_between': f"Column '{columns[0] if columns else 'unknown'}' values are not between {kwargs.get('min_value', 'N/A')} and {kwargs.get('max_value', 'N/A')}",
            'expect_column_values_to_be_in_set': f"Column '{columns[0] if columns else 'unknown'}' contains values not in allowed set",
            'expect_column_values_to_not_be_in_set': f"Column '{columns[0] if columns else 'unknown'}' contains disallowed values",
            'expect_column_values_to_match_regex': f"Column '{columns[0] if columns else 'unknown'}' values do not match required pattern",
            'expect_column_values_to_not_match_regex': f"Column '{columns[0] if columns else 'unknown'}' values match disallowed pattern",
            'expect_column_values_to_be_unique': f"Column '{columns[0] if columns else 'unknown'}' contains duplicate values",
            'expect_column_values_to_not_be_future_date': f"Column '{columns[0] if columns else 'unknown'}' contains future dates",
            'expect_column_values_to_not_be_older_than_years': f"Column '{columns[0] if columns else 'unknown'}' contains dates older than {kwargs.get('years', 'N/A')} years",
            'expect_column_values_to_be_after_column': f"Column '{columns[0] if columns else 'unknown'}' is not after column '{columns[1] if len(columns) > 1 else 'unknown'}'",
            'expect_column_values_to_be_after_column_if_populated': f"Column '{columns[0] if columns else 'unknown'}' (when populated) is not after column '{columns[1] if len(columns) > 1 else 'unknown'}'",
            'expect_column_values_to_not_be_before_column_if_populated': f"Column '{columns[0] if columns else 'unknown'}' (when populated) is before column '{columns[1] if len(columns) > 1 else 'unknown'}'",
            'expect_column_to_not_be_null_if_condition': f"Column '{kwargs.get('target_column', columns[1] if len(columns) > 1 else 'unknown')}' is null when '{kwargs.get('condition_column', columns[0] if columns else 'unknown')}' equals {kwargs.get('condition_value', True)}",
            'expect_column_values_conditional_date_comparison': f"Column '{columns[0] if columns else 'unknown'}' failed conditional date comparison",
            'expect_column_pair_values_A_to_be_greater_than_B': f"Column '{columns[0] if columns else 'unknown'}' is not greater than column '{columns[1] if len(columns) > 1 else 'unknown'}'",
            'expect_column_pair_values_to_be_equal': f"Columns '{columns[0] if columns else 'unknown'}' and '{columns[1] if len(columns) > 1 else 'unknown'}' are not equal",
            'expect_column_values_to_be_normalized': f"Column '{columns[0] if columns else 'unknown'}' contains values that could not be normalized",
            'expect_column_values_to_match_regex_and_replace': f"Column '{columns[0] if columns else 'unknown'}' contains values that do not match the required regex pattern",
        }
        
        # Get template or use default
        reason = reason_templates.get(expectation_type)
        if not reason:
            # Generic fallback
            reason = f"Failed expectation: {expectation_type}"
            if columns:
                reason += f" on column(s): {', '.join(columns)}"
        
        return reason
    
    def _add_failure_details(self, bad_df: DataFrame) -> DataFrame:
        """Add failure details (expectations, columns, reasons, isWarning) to bad DataFrame."""
        from pyspark.sql.functions import when, array, array_union, lit
        
        # Get the parsed rules for generating reasons
        parsed_rules = getattr(self, '_parsed_rules', [])
        rule_metadata = getattr(self, '_rule_metadata', [])
        
        # Initialize with empty arrays
        result_df = bad_df.withColumn("_dq_failed_expectations", array().cast(ArrayType(StringType())))
        result_df = result_df.withColumn("_dq_failed_columns", array().cast(ArrayType(StringType())))
        result_df = result_df.withColumn("_dq_failure_reasons", array().cast(ArrayType(StringType())))
        result_df = result_df.withColumn("_dq_is_warning", lit(False))  # Initialize isWarning flag
        
        # Process each rule and build arrays
        for rule_meta in rule_metadata:
            rule_name = rule_meta['rule_name']
            expectation_type = rule_meta['expectation_type']
            columns_involved = rule_meta['columns']
            is_warning = rule_meta.get('is_warning', False)
            
            # Find the corresponding rule for generating reason
            rule = None
            if parsed_rules and rule_meta['rule_index'] < len(parsed_rules):
                rule = parsed_rules[rule_meta['rule_index']]
            
            # Generate failure reason
            if rule:
                reason = self._generate_failure_reason(rule, columns_involved)
            else:
                reason = f"Failed expectation: {expectation_type}"
            
            # Check if this rule failed (rule column is False)
            rule_failed = ~col(rule_name)
            
            # Build column names string
            columns_str = ", ".join(columns_involved) if columns_involved else "N/A"
            
            # Add to arrays when rule fails using array_union
            result_df = result_df.withColumn(
                "_dq_failed_expectations",
                when(rule_failed,
                     array_union(col("_dq_failed_expectations"), array(lit(expectation_type)))
                ).otherwise(col("_dq_failed_expectations"))
            )
            
            result_df = result_df.withColumn(
                "_dq_failed_columns",
                when(rule_failed,
                     array_union(col("_dq_failed_columns"), array(lit(columns_str)))
                ).otherwise(col("_dq_failed_columns"))
            )
            
            result_df = result_df.withColumn(
                "_dq_failure_reasons",
                when(rule_failed,
                     array_union(col("_dq_failure_reasons"), array(lit(reason)))
                ).otherwise(col("_dq_failure_reasons"))
            )
            
            # Update isWarning flag: True if ANY failed rule is a warning
            result_df = result_df.withColumn(
                "_dq_is_warning",
                when(rule_failed & lit(is_warning), lit(True))
                .otherwise(col("_dq_is_warning"))
            )
        
        # Convert arrays to pipe-separated strings for readability
        result_df = result_df.withColumn(
            "_dq_failed_expectations",
            array_join(col("_dq_failed_expectations"), " | ")
        )
        
        result_df = result_df.withColumn(
            "_dq_failed_columns",
            array_join(col("_dq_failed_columns"), " | ")
        )
        
        result_df = result_df.withColumn(
            "_dq_failure_reasons",
            array_join(col("_dq_failure_reasons"), " | ")
        )
        
        # Drop rule columns and _dq_is_valid - they were only used internally to determine failures
        columns_to_keep = [c for c in result_df.columns 
                          if not c.startswith("rule_") and c != "_dq_is_valid"]
        result_df = result_df.select(*columns_to_keep)
        
        return result_df
    
    def _create_validation_summary(
        self, 
        original_df: DataFrame, 
        qualified_df: DataFrame, 
        bad_df: DataFrame,
        quality_rules: Union[str, Dict, List[Dict]]
    ) -> Dict[str, Any]:
        """Create a comprehensive validation summary."""
        total_count = original_df.count()
        qualified_count = qualified_df.count()
        bad_count = bad_df.count()
        
        return {
            "total_rows": total_count,
            "qualified_rows": qualified_count,
            "bad_rows": bad_count,
            "qualified_percentage": round((qualified_count / total_count * 100), 2) if total_count > 0 else 0,
            "bad_percentage": round((bad_count / total_count * 100), 2) if total_count > 0 else 0,
            "total_rules": len(self._parse_quality_rules(quality_rules)),
            "rules_applied": len(self._parse_quality_rules(quality_rules)),
            "validation_timestamp": str(uuid.uuid4())
        } 