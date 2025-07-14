import pandas as pd
import os
import numbers
# Assuming ValidationRules class is in validation_rules.py in the same directory
from validation_rules import ValidationRules

class ExcelValidator:
    def __init__(self, filepath, validation_config=None, read_excel_params=None):
        self.filepath = filepath
        self.df = None
        self.rules = ValidationRules()
        self.validation_config = validation_config if validation_config is not None else {}
        self.read_excel_params = read_excel_params if read_excel_params is not None else {}
        self.detailed_results = []

    def load_excel(self):
        # Clear previous results before a new load attempt
        self.detailed_results = []
        try:
            # Pass read_excel_params to pd.read_excel
            # Use dtype=str for relevant columns or the whole sheet to prevent premature coercion
            final_read_params = self.read_excel_params.copy()
            if 'dtype' not in final_read_params:
                 final_read_params['dtype'] = {}
            # Ensure columns expected to be numeric are read as strings initially if not specified otherwise
            numeric_cols_in_config = [col for col, type_str in self.validation_config.get("column_types", {}).items() if type_str.lower() in ['int', 'float']]
            for col in numeric_cols_in_config:
                 if col not in final_read_params['dtype']:
                     final_read_params['dtype'][col] = str


            self.df = pd.read_excel(self.filepath, **final_read_params)

            # Add load success result
            self.detailed_results.append({"rule": "load_excel", "status": "passed", "details": "File loaded successfully."})
            return True
        except FileNotFoundError:
            self.detailed_results.append({"rule": "load_excel", "status": "failed", "details": f"File not found at {self.filepath}"})
            self.df = None # Ensure df is None on failure
            return False
        except Exception as e:
            self.detailed_results.append({"rule": "load_excel", "status": "failed", "details": f"Error loading excel file: {e}"})
            self.df = None # Ensure df is None on failure
            return False


    def validate_data(self):
        # Preserve the load_excel result before clearing for validation results
        load_result = next((res for res in self.detailed_results if res["rule"] == "load_excel"), None)

        # Clear all results except the load result if it exists
        self.detailed_results = [load_result] if load_result else []


        # If load failed, validation cannot proceed. Add skipped results for other rules in config.
        if self.df is None:
             if not load_result: # Should already have a load_excel result from load_excel()
                 self.detailed_results.insert(0, {"rule": "load_excel", "status": "failed", "details": "DataFrame not loaded before validation."})
             self._add_skipped_results_for_config()
             return False # Validation fails because data is not loaded


        # Apply validation rules based on configuration
        if "expected_columns" in self.validation_config:
            result = self.rules.check_column_names(self.df, self.validation_config["expected_columns"])
            self.detailed_results.append(result)


        if "check_missing_values" in self.validation_config and self.validation_config["check_missing_values"]:
             result = self.rules.check_missing_values(self.df)
             self.detailed_results.append(result)


        if "column_types" in self.validation_config:
            for column, expected_type in self.validation_config["column_types"].items():
                result = self.rules.check_data_type(self.df, column, expected_type)
                self.detailed_results.append(result)

        if "check_unique_values" in self.validation_config:
             for column in self.validation_config["check_unique_values"]:
                 result = self.rules.check_unique_values(self.df, column)
                 self.detailed_results.append(result)


        if "column_ranges" in self.validation_config:
             for column, range_config in self.validation_config["column_ranges"].items():
                result = self.rules.check_range(self.df, column, range_config.get("min"), range_config.get("max"))
                self.detailed_results.append(result)


        # Check if any rule failed (including the load_excel rule)
        overall_status = "failed" if any(result["status"] == "failed" for result in self.detailed_results) else "passed"

        return overall_status == "passed"

    def _add_skipped_results_for_config(self):
        """Helper to add skipped results for rules in config when DataFrame is not loaded."""
        config = self.validation_config
        existing_rules = {res.get("rule") for res in self.detailed_results}
        existing_column_rules = {(res.get("rule"), res.get("column")) for res in self.detailed_results}

        if "expected_columns" in config and "check_column_names" not in existing_rules:
            self.detailed_results.append({"rule": "check_column_names", "status": "skipped", "details": "DataFrame not loaded"})
        if "check_missing_values" in config and config["check_missing_values"] and "check_missing_values" not in existing_rules:
             self.detailed_results.append({"rule": "check_missing_values", "status": "skipped", "details": "DataFrame not loaded"})
        if "column_types" in config:
            for column in config["column_types"]:
                 if ("check_data_type", column) not in existing_column_rules:
                     self.detailed_results.append({"rule": "check_data_type", "status": "skipped", "column": column, "details": "DataFrame not loaded"})
        if "check_unique_values" in config:
            for column in config["check_unique_values"]:
                 if ("check_unique_values", column) not in existing_column_rules:
                     self.detailed_results.append({"rule": "check_unique_values", "status": "skipped", "column": column, "details": "DataFrame not loaded"})
        if "column_ranges" in config:
            for column in config["column_ranges"]:
                 if ("check_range", column) not in existing_column_rules:
                     self.detailed_results.append({"rule": "check_range", "status": "skipped", "column": column, "details": "DataFrame not loaded"})


    def generate_report(self, output_filepath=None):
        """
        Generates a user-friendly report from detailed validation results.

        Args:
            output_filepath (str, optional): If provided, the report will be written
                                             to this file path. Defaults to None.

        Returns:
            str: The generated report string.
        """
        print(f"\nDEBUG: generate_report called. detailed_results: {self.detailed_results}") # Debug print

        if not self.detailed_results:
            report_content = "No validation results available. Run load_excel and validate_data first."
        else:
            report_lines = ["--- Validation Report ---"]

            # Sort results by status and then rule/column for consistent report generation
            # Put load_excel first, then failed, passed, skipped rules
            load_result = next((res for res in self.detailed_results if res["rule"] == "load_excel"), None)
            other_results = sorted([res for res in self.detailed_results if res["rule"] != "load_excel"],
                                   key=lambda x: (x["status"], x["rule"], x.get("column", "")))

            failed_rules = [res for res in other_results if res["status"] == "failed"]
            passed_rules = [res for res in other_results if res["status"] == "passed"]
            skipped_rules = [res for res in other_results if res["status"] == "skipped"]


            # Include overall status based on *all* results (including load)
            overall_status = 'FAILED' if any(res["status"] == "failed" for res in self.detailed_results) else 'PASSED'
            report_lines.append(f"\nOverall Status: {overall_status}\n")

            # Include load result first if it exists
            if load_result:
                details = load_result.get("details", "No specific details available.")
                status_info = f" (status: {load_result['status']})" # Always show status for load
                report_lines.append(f"- Rule '{load_result['rule']}'{status_info}: {details}")
                # Add a blank line after load result if there are other results
                if other_results:
                    report_lines.append("")


            if failed_rules:
                report_lines.append("Failed Rules:")
                for res in failed_rules:
                    details = res.get("details", "No specific details available.")
                    column_info = f" (Column: {res['column']})" if "column" in res else ""
                    report_lines.append(f"- Rule '{res['rule']}'{column_info}: {details}")
                # Add a blank line after failed rules if there are passed or skipped rules
                if passed_rules or skipped_rules:
                    report_lines.append("")


            if passed_rules:
                report_lines.append("Passed Rules:")
                for res in passed_rules:
                     column_info = f" (Column: {res['column']})" if "column" in res else ""
                     details_info = f": {res.get('details')}" if res.get('details') and res.get('details') != "File loaded successfully." else ""
                     status_info = " (status: passed)" if not details_info else "" # Add status if no other details
                     report_lines.append(f"- Rule '{res['rule']}'{column_info}{details_info}{status_info}")
                # Add a blank line after passed rules if there are skipped rules
                if skipped_rules:
                    report_lines.append("")


            if skipped_rules:
                report_lines.append("Skipped Rules:")
                for res in skipped_rules:
                     details = res.get("details", "No specific details available.")
                     column_info = f" (Column: {res['column']})" if "column" in res else ""
                     report_lines.append(f"- Rule '{res['rule']}'{column_info}: {details}")
                # No blank line needed after skipped rules


            report_lines.append("--- End of Report ---")
            report_content = "\n".join(report_lines)

        if output_filepath:
            try:
                with open(output_filepath, 'w') as f:
                    f.write(report_content)
                # Note: We don't add the report save result to detailed_results here
                # to avoid modifying the list during report generation which could
                # lead to issues or recursive behavior. The test can check file existence and content directly.
            except Exception as e:
                 print(f"Warning: Could not save report to {output_filepath}: {e}") # Also print warning to console


        return report_content
