import pandas as pd
import numbers

class ValidationRules:
    def check_column_names(self, df, expected_columns):
        """Checks if all expected columns are present."""
        if df is None:
             return {"rule": "check_column_names", "status": "skipped", "details": "DataFrame not loaded"}

        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            return {"rule": "check_column_names", "status": "failed", "details": f"Missing columns: {missing_columns}"}
        return {"rule": "check_column_names", "status": "passed"}

    def check_missing_values(self, df):
        """Checks for missing values in the entire DataFrame."""
        if df is None:
            return {"rule": "check_missing_values", "status": "skipped", "details": "DataFrame not loaded"}

        missing_info = df.isnull().sum()
        missing_columns_info = missing_info[missing_info > 0].to_dict()
        if missing_columns_info:
            return {"rule": "check_missing_values", "status": "failed", "details": f"Columns with missing values: {missing_columns_info}"}
        return {"rule": "check_missing_values", "status": "passed"}

    def check_data_type(self, df, column, expected_type):
        """Checks the data type of a specific column."""
        if df is None:
             return {"rule": "check_data_type", "status": "skipped", "column": column, "details": "DataFrame not loaded"}
        if column not in df.columns:
             return {"rule": "check_data_type", "status": "skipped", "column": column, "details": "Column not found"}

        actual_series = df[column]
        actual_dtype = actual_series.dtype
        expected_type_lower = expected_type.lower()

        # Handle numeric types (int, float)
        if expected_type_lower == 'int' or expected_type_lower == 'float':
            failed_indices = []
            # Iterate through non-null values to check if they are convertible
            for index, value in actual_series.dropna().items():
                try:
                    numeric_value = pd.to_numeric(value)
                    if expected_type_lower == 'int':
                        # Check if it's numerically integer (e.g., 3.0 is integer-like)
                        # Refined check: after converting to numeric, check if it has a fractional part
                        if not isinstance(numeric_value, numbers.Integral) and (isinstance(numeric_value, numbers.Real) and numeric_value % 1 != 0):
                             failed_indices.append(index)
                             continue # Found a non-integer float, fail for this value
                    # For float, any numeric value is acceptable
                except (ValueError, TypeError):
                    # Value could not be converted to a number
                    failed_indices.append(index)

            if failed_indices:
                return {"rule": "check_data_type", "status": "failed", "column": column, "details": f"Expected type '{expected_type}', but non-numeric or non-integer values found at indices {failed_indices}."}

            # If no non-numeric/non-integer values found, the type check passes for numeric types
            return {"rule": "check_data_type", "status": "passed", "column": column}


        # Handle non-numeric types explicitly
        elif expected_type_lower in ['object', 'str']:
             # Check if the dtype is explicitly object or a pandas string dtype, or if all non-null values are strings
             if pd.api.types.is_object_dtype(actual_dtype) or pd.api.types.is_string_dtype(actual_dtype) or actual_series.dropna().apply(lambda x: isinstance(x, str)).all():
                  return {"rule": "check_data_type", "status": "passed", "column": column}
             # If neither of the above, it fails
             return {"rule": "check_data_type", "status": "failed", "column": column, "details": f"Expected type '{expected_type}', but found '{actual_dtype}'."}

        elif expected_type_lower == 'bool':
             # Check for boolean dtypes
             if pd.api.types.is_bool_dtype(actual_dtype):
                  return {"rule": "check_data_type", "status": "passed", "column": column}
             # If not boolean dtype
             return {"rule": "check_data_type", "status": "failed", "column": column, "details": f"Expected type 'bool', but found '{actual_dtype}'."}

        # If the expected type was not recognized
        return {"rule": "check_data_type", "status": "failed", "column": column, "details": f"Expected type '{expected_type}' is not supported."}


    def check_range(self, df, column, min_value=None, max_value=None):
        """Checks if values in a column are within a specified range."""
        if df is None:
             return {"rule": "check_range", "status": "skipped", "column": column, "details": "DataFrame not loaded"}
        if column not in df.columns:
             return {"rule": "check_range", "status": "skipped", "column": column, "details": "Column not found"}

        failures = []
        actual_series = df[column]

        # Ensure column is numeric before comparison, handle non-numeric gracefully
        # Attempt to coerce to numeric, identifying non-numeric values
        numeric_series = pd.to_numeric(actual_series, errors='coerce')
        non_numeric_mask = actual_series.notnull() & numeric_series.isnull()

        if non_numeric_mask.any():
             non_numeric_indices = actual_series[non_numeric_mask].index.tolist()
             failures.append(f"Column '{column}' contains non-numeric values that prevent range check at indices {non_numeric_indices}.")

        # Now perform range check on the coerced numeric series (NaNs from coercion or original data are ignored by comparison)
        if pd.api.types.is_numeric_dtype(numeric_series.dtype):
             if min_value is not None:
                 failed_min = numeric_series[numeric_series < min_value]
                 if not failed_min.empty:
                      failures.append(f"Values below minimum ({min_value}) found at indices: {failed_min.index.tolist()}")
             if max_value is not None:
                 failed_max = numeric_series[numeric_series > max_value]
                 if not failed_max.empty:
                     failures.append(f"Values above maximum ({max_value}) found at indices: {failed_max.index.tolist()}")
        elif not non_numeric_mask.any(): # If not numeric dtype after coercion and no non-numeric strings were found (e.g., all NaNs)
             failures.append(f"Column '{column}' is not numeric and cannot be checked for range.")


        if failures:
            return {"rule": "check_range", "status": "failed", "column": column, "details": "; ".join(failures)}
        return {"rule": "check_range", "status": "passed", "column": column}

    def check_unique_values(self, df, column):
        """Checks for unique non-null values in a specified column."""
        if df is None:
             return {"rule": "check_unique_values", "status": "skipped", "column": column, "details": "DataFrame not loaded"}
        if column not in df.columns:
             return {"rule": "check_unique_values", "status": "skipped", "column": column, "details": "Column not found"}

        # Check for duplicates in non-null values
        if df[column].dropna().duplicated().any():
            # Optionally find duplicated values or indices for more detail
            duplicated_values = df[column][df[column].duplicated(keep=False)].unique().tolist()
            return {"rule": "check_unique_values", "status": "failed", "column": column, "details": f"Duplicate values found in column '{column}'. Duplicated values (showing first occurrence): {duplicated_values}"}

        return {"rule": "check_unique_values", "status": "passed", "column": column}
