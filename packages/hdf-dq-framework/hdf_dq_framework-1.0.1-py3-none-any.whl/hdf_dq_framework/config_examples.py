"""
Configuration examples for the Data Quality Framework.

This module provides pre-built configurations for common data quality scenarios
that can be used with the DQFramework to filter DataFrames.
"""

from typing import Dict, Any, List


class DQConfigExamples:
    """
    Provides example configurations for common data quality filtering scenarios.
    """
    
    @staticmethod
    def customer_data_quality() -> Dict[str, Any]:
        """
        Customer data quality rules focusing on key customer attributes.
        
        Returns:
            Dictionary with expectations for customer data validation
        """
        return {
            "expectations": [
                {
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": "customer_id"}
                },
                {
                    "expectation_type": "expect_column_values_to_be_unique",
                    "kwargs": {"column": "customer_id"}
                },
                {
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": "email"}
                },
                {
                    "expectation_type": "expect_column_values_to_match_regex",
                    "kwargs": {
                        "column": "email",
                        "regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                    }
                },
                {
                    "expectation_type": "expect_column_values_to_be_between",
                    "kwargs": {"column": "age", "min_value": 13, "max_value": 120}
                },
                {
                    "expectation_type": "expect_column_values_to_be_in_set",
                    "kwargs": {"column": "status", "value_set": ["active", "inactive", "suspended"]}
                }
            ],
            "meta": {
                "description": "Customer data quality filtering rules",
                "use_case": "Filter out invalid customer records"
            }
        }
    
    @staticmethod
    def financial_transaction_quality() -> Dict[str, Any]:
        """
        Financial transaction data quality rules.
        
        Returns:
            Dictionary with expectations for financial transaction validation
        """
        return {
            "expectations": [
                {
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": "transaction_id"}
                },
                {
                    "expectation_type": "expect_column_values_to_be_unique",
                    "kwargs": {"column": "transaction_id"}
                },
                {
                    "expectation_type": "expect_column_values_to_be_between",
                    "kwargs": {"column": "amount", "min_value": 0.01, "max_value": 1000000}
                },
                {
                    "expectation_type": "expect_column_values_to_be_in_set",
                    "kwargs": {"column": "currency", "value_set": ["USD", "EUR", "GBP", "JPY", "CAD"]}
                },
                {
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": "transaction_date"}
                },
                {
                    "expectation_type": "expect_column_values_to_be_in_set",
                    "kwargs": {"column": "transaction_type", "value_set": ["credit", "debit", "transfer", "payment"]}
                }
            ],
            "meta": {
                "description": "Financial transaction quality filtering",
                "compliance": "Removes invalid transactions for financial reporting"
            }
        }
    
    @staticmethod
    def product_catalog_quality() -> Dict[str, Any]:
        """
        Product catalog data quality rules.
        
        Returns:
            Dictionary with expectations for product data validation
        """
        return {
            "expectations": [
                {
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": "product_id"}
                },
                {
                    "expectation_type": "expect_column_values_to_be_unique",
                    "kwargs": {"column": "product_id"}
                },
                {
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": "product_name"}
                },
                {
                    "expectation_type": "expect_column_value_lengths_to_be_between",
                    "kwargs": {"column": "product_name", "min_value": 2, "max_value": 200}
                },
                {
                    "expectation_type": "expect_column_values_to_be_between",
                    "kwargs": {"column": "price", "min_value": 0, "max_value": 100000}
                },
                {
                    "expectation_type": "expect_column_values_to_be_in_set",
                    "kwargs": {"column": "category", "value_set": ["electronics", "clothing", "home", "books", "toys", "sports"]}
                },
                {
                    "expectation_type": "expect_column_values_to_be_in_set",
                    "kwargs": {"column": "status", "value_set": ["active", "discontinued", "out_of_stock"]}
                }
            ],
            "meta": {
                "description": "Product catalog quality filtering",
                "business_rules": ["Valid product information for customer-facing catalog"]
            }
        }
    
    @staticmethod
    def healthcare_patient_quality() -> Dict[str, Any]:
        """
        Healthcare patient data quality rules.
        
        Returns:
            Dictionary with expectations for patient data validation
        """
        return {
            "expectations": [
                {
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": "patient_id"}
                },
                {
                    "expectation_type": "expect_column_values_to_be_unique",
                    "kwargs": {"column": "patient_id"}
                },
                {
                    "expectation_type": "expect_column_values_to_match_regex",
                    "kwargs": {"column": "patient_id", "regex": r"^P\d{8}$"}
                },
                {
                    "expectation_type": "expect_column_values_to_be_between",
                    "kwargs": {"column": "age", "min_value": 0, "max_value": 150}
                },
                {
                    "expectation_type": "expect_column_values_to_be_in_set",
                    "kwargs": {"column": "gender", "value_set": ["M", "F", "O", "Unknown"]}
                },
                {
                    "expectation_type": "expect_column_values_to_match_regex",
                    "kwargs": {"column": "medical_record_number", "regex": r"^MRN\d{8}$"}
                }
            ],
            "meta": {
                "description": "Healthcare patient data quality filtering",
                "compliance": "HIPAA compliant patient data validation"
            }
        }
    
    @staticmethod
    def sales_order_quality() -> Dict[str, Any]:
        """
        Sales order data quality rules.
        
        Returns:
            Dictionary with expectations for sales order validation
        """
        return {
            "expectations": [
                {
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": "order_id"}
                },
                {
                    "expectation_type": "expect_column_values_to_be_unique",
                    "kwargs": {"column": "order_id"}
                },
                {
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": "customer_id"}
                },
                {
                    "expectation_type": "expect_column_values_to_be_between",
                    "kwargs": {"column": "order_total", "min_value": 0, "max_value": 50000}
                },
                {
                    "expectation_type": "expect_column_values_to_be_between",
                    "kwargs": {"column": "quantity", "min_value": 1, "max_value": 1000}
                },
                {
                    "expectation_type": "expect_column_values_to_be_in_set",
                    "kwargs": {"column": "order_status", "value_set": ["pending", "confirmed", "shipped", "delivered", "cancelled"]}
                }
            ],
            "meta": {
                "description": "Sales order quality filtering",
                "business_impact": "Ensures clean data for sales analytics and reporting"
            }
        }
    
    @staticmethod
    def employee_data_quality() -> Dict[str, Any]:
        """
        Employee data quality rules.
        
        Returns:
            Dictionary with expectations for employee data validation
        """
        return {
            "expectations": [
                {
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": "employee_id"}
                },
                {
                    "expectation_type": "expect_column_values_to_be_unique",
                    "kwargs": {"column": "employee_id"}
                },
                {
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": "email"}
                },
                {
                    "expectation_type": "expect_column_values_to_match_regex",
                    "kwargs": {"column": "email", "regex": r"^[a-zA-Z0-9._%+-]+@company\.com$"}
                },
                {
                    "expectation_type": "expect_column_values_to_be_between",
                    "kwargs": {"column": "salary", "min_value": 30000, "max_value": 500000}
                },
                {
                    "expectation_type": "expect_column_values_to_be_in_set",
                    "kwargs": {"column": "department", "value_set": ["IT", "HR", "Finance", "Marketing", "Sales", "Operations"]}
                },
                {
                    "expectation_type": "expect_column_values_to_be_in_set",
                    "kwargs": {"column": "employment_status", "value_set": ["active", "inactive", "terminated"]}
                }
            ],
            "meta": {
                "description": "Employee data quality filtering",
                "privacy": "Ensures valid employee records for HR systems"
            }
        }
    
    @staticmethod
    def simple_null_check() -> List[Dict[str, Any]]:
        """
        Simple null check configuration for any dataset.
        
        Returns:
            List of expectations for basic null validation
        """
        return [
            {
                "expectation_type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": "id"}
            }
        ]
    
    @staticmethod
    def data_type_validation() -> List[Dict[str, Any]]:
        """
        Data type validation example.
        
        Returns:
            List of expectations for data type checking
        """
        return [
            {
                "expectation_type": "expect_column_values_to_be_of_type",
                "kwargs": {"column": "id", "type_": "int"}
            },
            {
                "expectation_type": "expect_column_values_to_be_of_type",
                "kwargs": {"column": "name", "type_": "string"}
            },
            {
                "expectation_type": "expect_column_values_to_be_of_type",
                "kwargs": {"column": "amount", "type_": "float"}
            }
        ]
    
    @staticmethod
    def regex_validation_patterns() -> Dict[str, Any]:
        """
        Common regex validation patterns.
        
        Returns:
            Dictionary with various regex validation examples
        """
        return {
            "expectations": [
                {
                    "expectation_type": "expect_column_values_to_match_regex",
                    "kwargs": {"column": "phone", "regex": r"^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$"}
                },
                {
                    "expectation_type": "expect_column_values_to_match_regex",
                    "kwargs": {"column": "zip_code", "regex": r"^\d{5}(-\d{4})?$"}
                },
                {
                    "expectation_type": "expect_column_values_to_match_regex",
                    "kwargs": {"column": "credit_card", "regex": r"^\d{4}-?\d{4}-?\d{4}-?\d{4}$"}
                },
                {
                    "expectation_type": "expect_column_values_to_match_regex",
                    "kwargs": {"column": "ssn", "regex": r"^\d{3}-?\d{2}-?\d{4}$"}
                }
            ],
            "meta": {
                "description": "Common regex patterns for data validation",
                "patterns": {
                    "phone": "US phone number format",
                    "zip_code": "US ZIP code format",
                    "credit_card": "Credit card number format",
                    "ssn": "Social Security Number format"
                }
            }
        }
    
    @staticmethod
    def advanced_expectations_showcase() -> Dict[str, Any]:
        """
        Showcase of advanced Great Expectations expectation types.
        
        Returns:
            Dictionary with advanced expectations for demonstration
        """
        return {
            "expectations": [
                # Date format validation
                {
                    "expectation_type": "expect_column_values_to_match_strftime_format",
                    "kwargs": {"column": "order_date", "strftime_format": "%Y-%m-%d"}
                },
                # Date parsing validation
                {
                    "expectation_type": "expect_column_values_to_be_dateutil_parseable",
                    "kwargs": {"column": "order_date"}
                },
                # JSON validation
                {
                    "expectation_type": "expect_column_values_to_be_json_parseable",
                    "kwargs": {"column": "metadata"}
                },
                # String length exact match
                {
                    "expectation_type": "expect_column_value_lengths_to_equal",
                    "kwargs": {"column": "product_code", "value": 8}
                },
                # Column pair comparison
                {
                    "expectation_type": "expect_column_pair_values_A_to_be_greater_than_B",
                    "kwargs": {"column_A": "end_date", "column_B": "start_date"}
                },
                # Multi-column uniqueness
                {
                    "expectation_type": "expect_multicolumn_values_to_be_unique",
                    "kwargs": {"column_list": ["customer_id", "order_date", "product_id"]}
                },
                # Column values to be increasing
                {
                    "expectation_type": "expect_column_values_to_be_increasing",
                    "kwargs": {"column": "sequence_number", "strictly": True}
                },
                # Table structure validation
                {
                    "expectation_type": "expect_table_column_count_to_be_between",
                    "kwargs": {"min_value": 5, "max_value": 20}
                }
            ],
            "meta": {
                "description": "Advanced Great Expectations showcase",
                "features": [
                    "Date/time validation",
                    "JSON structure validation", 
                    "Multi-column relationships",
                    "Sequential data validation",
                    "Table structure validation"
                ]
            }
        }
    
    @staticmethod
    def statistical_expectations() -> Dict[str, Any]:
        """
        Statistical expectations for data analysis.
        
        Returns:
            Dictionary with statistical validation expectations
        """
        return {
            "expectations": [
                # Mean validation
                {
                    "expectation_type": "expect_column_mean_to_be_between",
                    "kwargs": {"column": "price", "min_value": 10.0, "max_value": 1000.0}
                },
                # Standard deviation validation
                {
                    "expectation_type": "expect_column_stdev_to_be_between", 
                    "kwargs": {"column": "price", "min_value": 1.0, "max_value": 100.0}
                },
                # Unique value count validation
                {
                    "expectation_type": "expect_column_unique_value_count_to_be_between",
                    "kwargs": {"column": "category", "min_value": 3, "max_value": 10}
                },
                # Min/Max validation
                {
                    "expectation_type": "expect_column_max_to_be_between",
                    "kwargs": {"column": "quantity", "min_value": 1, "max_value": 1000}
                },
                {
                    "expectation_type": "expect_column_min_to_be_between",
                    "kwargs": {"column": "quantity", "min_value": 0, "max_value": 1}
                },
                # Sum validation
                {
                    "expectation_type": "expect_column_sum_to_be_between",
                    "kwargs": {"column": "total_amount", "min_value": 1000, "max_value": 1000000}
                }
            ],
            "meta": {
                "description": "Statistical data quality expectations",
                "use_case": "Validate statistical properties of numeric columns"
            }
        }
    
    @staticmethod
    def complex_business_rules() -> Dict[str, Any]:
        """
        Complex business rule validations using multiple expectation types.
        
        Returns:
            Dictionary with complex business validation rules
        """
        return {
            "expectations": [
                # Basic required fields
                {
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": "transaction_id"}
                },
                # ID format validation
                {
                    "expectation_type": "expect_column_values_to_match_regex",
                    "kwargs": {"column": "transaction_id", "regex": r"^TXN\d{8}$"}
                },
                # Amount validation with business rules
                {
                    "expectation_type": "expect_column_values_to_be_between",
                    "kwargs": {"column": "amount", "min_value": 0.01, "max_value": 10000.0}
                },
                # Date format validation
                {
                    "expectation_type": "expect_column_values_to_match_strftime_format",
                    "kwargs": {"column": "transaction_date", "strftime_format": "%Y-%m-%d %H:%M:%S"}
                },
                # Status validation
                {
                    "expectation_type": "expect_column_values_to_be_in_set",
                    "kwargs": {"column": "status", "value_set": ["pending", "completed", "failed", "cancelled"]}
                },
                # Cross-column validation
                {
                    "expectation_type": "expect_column_pair_values_A_to_be_greater_than_B",
                    "kwargs": {"column_A": "amount", "column_B": "fee", "or_equal": True}
                },
                # Unique transaction validation
                {
                    "expectation_type": "expect_compound_columns_to_be_unique",
                    "kwargs": {"column_list": ["transaction_id", "merchant_id"]}
                },
                # Table structure validation
                {
                    "expectation_type": "expect_table_row_count_to_be_between",
                    "kwargs": {"min_value": 1, "max_value": 1000000}
                }
            ],
            "meta": {
                "description": "Complex business rule validation suite",
                "business_rules": [
                    "All transactions must have valid IDs",
                    "Amounts must be positive and within limits",
                    "Dates must follow standard format",
                    "Status must be from approved list",
                    "Amount must be >= fee",
                    "Transaction+Merchant combinations must be unique"
                ]
            }
        }
    
    @staticmethod
    def get_all_examples() -> Dict[str, Dict[str, Any]]:
        """
        Get all available configuration examples.
        
        Returns:
            Dictionary mapping example names to their configurations
        """
        return {
            "customer_data_quality": DQConfigExamples.customer_data_quality(),
            "financial_transaction_quality": DQConfigExamples.financial_transaction_quality(),
            "product_catalog_quality": DQConfigExamples.product_catalog_quality(),
            "healthcare_patient_quality": DQConfigExamples.healthcare_patient_quality(),
            "sales_order_quality": DQConfigExamples.sales_order_quality(),
            "employee_data_quality": DQConfigExamples.employee_data_quality(),
            "regex_validation_patterns": DQConfigExamples.regex_validation_patterns(),
            "advanced_expectations_showcase": DQConfigExamples.advanced_expectations_showcase(),
            "statistical_expectations": DQConfigExamples.statistical_expectations(),
            "complex_business_rules": DQConfigExamples.complex_business_rules()
        } 