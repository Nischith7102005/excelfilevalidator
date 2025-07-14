import unittest
import pandas as pd
import os
# Assuming ExcelValidator class is in excel_validator.py in the same directory
from excel_validator import ExcelValidator

class TestExcelValidator(unittest.TestCase):

    def setUp(self):
        """Set up dummy data and file before each test."""
        self.dummy_filepath = 'test_dummy_data.xlsx'
        self.report_filepath = 'test_validation_report.txt' # Define a path for report file

    def tearDown(self):
        """Clean up dummy file and report file after each test."""
        if os.path.exists(self.dummy_filepath):
            os.remove(self.dummy_filepath)
        if os.path.exists(self.report_filepath): # Clean up report file
            os.remove(self.report_filepath)

    def create_dummy_excel(self, data):
        """Helper to create a dummy Excel file."""
        df = pd.DataFrame(data)
        df.to_excel(self.dummy_filepath, index=False)

    def test_successful_validation(self):
        """Test validation with data that should pass all rules."""
        data = {
            'ID': [1, 2, 3],
            'Name': ['A', 'B', 'C'],
            'Value': [10.1, 20.2, 30.3],
            'Count': [100, 150, 200]
        }
        self.create_dummy_excel(data)
        validation_config = {
            "expected_columns": ["ID", "Name", "Value", "Count"],
            "check_missing_values": True,
            "column_types": {
                "ID": "int",
                "Name": "object",
                "Value": "float",
                "Count": "int"
            },
            "column_ranges": {
                "ID": {"min": 1, "max": 3},
                "Count": {"min": 50, "max": 300}
            }
        }
        validator = ExcelValidator(self.dummy_filepath, validation_config)
        self.assertTrue(validator.load_excel())
        self.assertTrue(validator.validate_data())
        report = validator.generate_report()
        self.assertIn("Overall Status: PASSED", report)
        self.assertNotIn("Failed Rules:", report)
        # Assert the load_excel rule is in the report
        self.assertIn("- Rule 'load_excel' (status: passed)", report)
        self.assertIn("- Rule 'check_column_names' (status: passed)", report)
        self.assertIn("- Rule 'check_missing_values' (status: passed)", report)
        self.assertIn("- Rule 'check_data_type' (Column: ID) (status: passed)", report)
        self.assertIn("- Rule 'check_data_type' (Column: Name) (status: passed)", report)
        self.assertIn("- Rule 'check_data_type' (Column: Value) (status: passed)", report)
        self.assertIn("- Rule 'check_data_type' (Column: Count) (status: passed)", report)
        self.assertIn("- Rule 'check_range' (Column: ID) (status: passed)", report)
        self.assertIn("- Rule 'check_range' (Column: Count) (status: passed)", report)


    def test_validation_missing_column(self):
        """Test validation with a missing expected column."""
        data = {
            'ID': [1, 2, 3],
            'Name': ['A', 'B', 'C']
        }
        self.create_dummy_excel(data)
        validation_config = {
            "expected_columns": ["ID", "Name", "Value"] # 'Value' is missing
        }
        validator = ExcelValidator(self.dummy_filepath, validation_config)
        self.assertTrue(validator.load_excel())
        self.assertFalse(validator.validate_data())
        report = validator.generate_report()
        self.assertIn("Overall Status: FAILED", report)
        self.assertIn("Failed Rules:", report)
        self.assertIn("- Rule 'check_column_names': Missing columns: ['Value']", report)
        # Assert the load_excel rule is in the report
        self.assertIn("- Rule 'load_excel' (status: passed)", report)


    def test_validation_missing_values(self):
        """Test validation with missing values."""
        data = {
            'ID': [1, 2, None], # Missing value
            'Name': ['A', 'B', 'C'],
            'Value': [10.1, None, 30.3] # Missing value
        }
        self.create_dummy_excel(data)
        validation_config = {
            "check_missing_values": True
        }
        validator = ExcelValidator(self.dummy_filepath, validation_config)
        self.assertTrue(validator.load_excel())
        self.assertFalse(validator.validate_data())
        report = validator.generate_report()
        self.assertIn("Overall Status: FAILED", report)
        self.assertIn("Failed Rules:", report)
        self.assertIn("- Rule 'check_missing_values': Columns with missing values:", report)
        self.assertIn("'ID': 1", report)
        self.assertIn("'Value': 1", report)
        # Assert the load_excel rule is in the report
        self.assertIn("- Rule 'load_excel' (status: passed)", report)


    def test_validation_incorrect_data_type(self):
        """Test validation with incorrect data types."""
        data = {
            'ID': [1, 2, '3'], # Incorrect type (string)
            'Name': ['A', 'B', 'C'],
            'Value': [10.1, 20.2, 30] # Incorrect type (int instead of float)
        }
        self.create_dummy_excel(data)
        validation_config = {
            "column_types": {
                "ID": "int",
                "Value": "float"
            }
        }
        # No explicit dtype='object' needed here due to updated load_excel
        validator = ExcelValidator(self.dummy_filepath, validation_config)

        self.assertTrue(validator.load_excel())
        self.assertFalse(validator.validate_data()) # Expecting failure
        report = validator.generate_report()

        self.assertIn("Overall Status: FAILED", report)
        self.assertIn("Failed Rules:", report)

        # 'ID' column should fail because it contains a non-numeric string '3'
        self.assertIn("- Rule 'check_data_type' (Column: ID): Expected type 'int', but non-numeric or non-integer values found at indices [2].", report)

        # 'Value' column contains 10.1 (float), 20.2 (float), and 30 (int).
        # When read as string, these will be '10.1', '20.2', '30'.
        # The check_data_type for 'float' will iterate and successfully convert all to numeric.
        # So the 'Value' column type check should pass.
        self.assertIn("- Rule 'check_data_type' (Column: Value)", report) # Check if the rule was run for Value
        self.assertIn("- Rule 'check_data_type' (Column: Value) (status: passed)", report) # Assert that the type check for Value column passed

        # Assert the load_excel rule is in the report
        self.assertIn("- Rule 'load_excel' (status: passed)", report)


    def test_validation_out_of_range_values(self):
        """Test validation with values outside the specified range."""
        data = {
            'Count': [100, 40, 250] # 40 is below min, 250 is above max
        }
        self.create_dummy_excel(data)
        validation_config = {
            "column_ranges": {
                "Count": {"min": 50, "max": 200}
            }
        }
        validator = ExcelValidator(self.dummy_filepath, validation_config)
        self.assertTrue(validator.load_excel())
        self.assertFalse(validator.validate_data())
        report = validator.generate_report()
        self.assertIn("Overall Status: FAILED", report)
        self.assertIn("Failed Rules:", report)
        self.assertIn("Values below minimum (50) found at indices: [1]; Values above maximum (200) found at indices: [2]", report)
        # Assert the load_excel rule is in the report
        self.assertIn("- Rule 'load_excel' (status: passed)", report)


    def test_validation_non_existent_column_in_config(self):
        """Test validation with a non-existent column specified in config."""
        data = {
            'ID': [1, 2, 3]
        }
        self.create_dummy_excel(data)
        validation_config = {
            "column_types": {
                "ID": "int",
                "NonExistentColumn": "float" # This column doesn't exist
            },
            "column_ranges": {
                "ID": {"min": 1, "max": 3},
                "AnotherNonExistentColumn": {"min": 0, "max": 100} # This column doesn't exist
            }
        }
        validator = ExcelValidator(self.dummy_filepath, validation_config)
        self.assertTrue(validator.load_excel())
        self.assertTrue(validator.validate_data()) # Should pass as non-existent columns are skipped
        report = validator.generate_report()
        self.assertIn("Overall Status: PASSED", report) # Overall status should be PASSED
        self.assertNotIn("Failed Rules:", report)
        self.assertIn("Skipped Rules:", report)
        self.assertIn("- Rule 'check_data_type' (Column: NonExistentColumn): Column not found", report)
        self.assertIn("- Rule 'check_range' (Column: AnotherNonExistentColumn): Column not found", report)
        # Assert the load_excel rule is in the report
        self.assertIn("- Rule 'load_excel' (status: passed)", report)


    def test_validation_edge_cases_range(self):
        """Test range checks at the boundaries."""
        data = {
            'Value': [0, 50, 100] # Min, middle, max
        }
        self.create_dummy_excel(data)
        validation_config = {
            "column_ranges": {
                "Value": {"min": 0, "max": 100}
            }
        }
        validator = ExcelValidator(self.dummy_filepath, validation_config)
        self.assertTrue(validator.load_excel())
        self.assertTrue(validator.validate_data()) # Should pass
        report = validator.generate_report()
        self.assertIn("Overall Status: PASSED", report)
        self.assertNotIn("Failed Rules:", report)
        # Assert the load_excel rule is in the report
        self.assertIn("- Rule 'load_excel' (status: passed)", report)
        self.assertIn("- Rule 'check_range' (Column: Value) (status: passed)", report)


        data_fail = {
            'Value': [-1, 0, 100, 101] # Below min and above max
        }
        self.create_dummy_excel(data_fail)
        validation_config_fail = {
            "column_ranges": {
                "Value": {"min": 0, "max": 100}
            }
        }
        validator_fail = ExcelValidator(self.dummy_filepath, validation_config_fail)
        self.assertTrue(validator_fail.load_excel())
        self.assertFalse(validator_fail.validate_data()) # Should fail
        report_fail = validator_fail.generate_report()
        self.assertIn("Overall Status: FAILED", report_fail)
        self.assertIn("Failed Rules:", report_fail)
        self.assertIn("Values below minimum (0) found at indices: [0]", report_fail)
        self.assertIn("Values above maximum (100) found at indices: [3]", report_fail)
        # Assert the load_excel rule is in the report
        self.assertIn("- Rule 'load_excel' (status: passed)", report_fail)


    def test_validation_file_not_found(self):
        """Test handling of a non-existent Excel file."""
        validation_config = {
            "expected_columns": ["ID"],
            "column_types": {"Name": "str"},
            "column_ranges": {"Age": {"min": 0}}
        }
        validator = ExcelValidator('non_existent_file.xlsx', validation_config)
        # Load should fail
        self.assertFalse(validator.load_excel())
        # Validate should return False because data wasn't loaded, but still process config for skipped rules
        self.assertFalse(validator.validate_data())
        report = validator.generate_report()
        # Overall status should be FAILED because load_excel failed
        self.assertIn("Overall Status: FAILED", report)
        self.assertIn("Failed Rules:", report)
        self.assertIn("- Rule 'load_excel': File not found at non_existent_file.xlsx", report)
        self.assertIn("Skipped Rules:", report)
        self.assertIn("- Rule 'check_column_names': DataFrame not loaded", report)
        self.assertIn("- Rule 'check_data_type' (Column: Name): DataFrame not loaded", report)
        self.assertIn("- Rule 'check_range' (Column: Age): DataFrame not loaded", report)

    def test_validation_type_mixed_numeric_string(self):
        """Test data type validation with a column containing mixed numeric and string values."""
        data = {
            'Mixed': [1, 2, 'three', 4.0, None]
        }
        self.create_dummy_excel(data)
        validation_config = {
            "column_types": {
                "Mixed": "int"
            }
        }
        # No explicit dtype='object' needed here due to updated load_excel
        validator = ExcelValidator(self.dummy_filepath, validation_config)

        self.assertTrue(validator.load_excel())
        self.assertFalse(validator.validate_data())
        report = validator.generate_report()

        self.assertIn("Overall Status: FAILED", report)
        self.assertIn("Failed Rules:", report)
        # The non-numeric value 'three' should cause the int check to fail
        self.assertIn("- Rule 'check_data_type' (Column: Mixed): Expected type 'int', but non-numeric or non-integer values found at indices [2].", report)
        # Assert the load_excel rule is in the report
        self.assertIn("- Rule 'load_excel' (status: passed)", report)


        validation_config_float = {
            "column_types": {
                "Mixed": "float"
            }
        }
        # No explicit dtype='object' needed here due to updated load_excel
        validator_float = ExcelValidator(self.dummy_filepath, validation_config_float)

        self.assertTrue(validator_float.load_excel())
        self.assertFalse(validator_float.validate_data()) # Should still fail as 'three' is not float
        report_float = validator_float.generate_report()
        self.assertIn("Overall Status: FAILED", report_float)
        self.assertIn("Failed Rules:", report_float)
        # The non-numeric value 'three' should cause the float check to fail
        self.assertIn("- Rule 'check_data_type' (Column: Mixed): Expected type 'float', but non-numeric or non-integer values found at indices [2].", report_float)
        # Assert the load_excel rule is in the report
        self.assertIn("- Rule 'load_excel' (status: passed)", report_float)

    def test_validation_type_float_as_int(self):
        """Test data type validation when a column contains floats but expected is int."""
        data = {
            'FloatCol': [1.0, 2.0, 3.5] # Contains floats, one not an integer
        }
        self.create_dummy_excel(data)
        validation_config = {
            "column_types": {
                "FloatCol": "int"
            }
        }
        validator = ExcelValidator(self.dummy_filepath, validation_config)
        self.assertTrue(validator.load_excel())
        self.assertFalse(validator.validate_data()) # Should fail due to 3.5
        report = validator.generate_report()
        self.assertIn("Overall Status: FAILED", report)
        self.assertIn("Failed Rules:", report)
        # The message should indicate that it found floats that are not integers.
        self.assertIn("- Rule 'check_data_type' (Column: FloatCol): Expected type 'int', but non-numeric or non-integer values found at indices [2].", report) # Or similar float dtype
        # Assert the load_excel rule is in the report
        self.assertIn("- Rule 'load_excel' (status: passed)", report)

    def test_validation_type_int_as_float(self):
        """Test data type validation when a column contains integers but expected is float."""
        data = {
            'IntCol': [1, 2, 3] # Contains integers
        }
        self.create_dummy_excel(data)
        validation_config = {
            "column_types": {
                "IntCol": "float"
            }
        }
        validator = ExcelValidator(self.dummy_filepath, validation_config)
        self.assertTrue(validator.load_excel())
        self.assertTrue(validator.validate_data()) # Should pass, integers are valid floats
        report = validator.generate_report()
        self.assertIn("Overall Status: PASSED", report)
        self.assertNotIn("Failed Rules:", report)
        # Corrected assertion for passed rule without extra details
        self.assertIn("- Rule 'check_data_type' (Column: IntCol) (status: passed)", report)
        # Assert the load_excel rule is in the report
        self.assertIn("- Rule 'load_excel' (status: passed)", report)

    def test_validation_unique_values(self):
        """Test validation for unique values."""
        # Test case with unique values
        data_unique = {
            'ID': [1, 2, 3, 4],
            'Name': ['A', 'B', 'C', 'D']
        }
        self.create_dummy_excel(data_unique)
        validation_config_unique = {
            "check_unique_values": ["ID"]
        }
        validator_unique = ExcelValidator(self.dummy_filepath, validation_config_unique)
        self.assertTrue(validator_unique.load_excel())
        self.assertTrue(validator_unique.validate_data()) # Should pass
        report_unique = validator_unique.generate_report()
        self.assertIn("Overall Status: PASSED", report_unique)
        self.assertNotIn("Failed Rules:", report_unique)
        self.assertIn("- Rule 'check_unique_values' (Column: ID) (status: passed)", report_unique)
        self.assertIn("- Rule 'load_excel' (status: passed)", report_unique)


        # Test case with duplicate values
        data_duplicate = {
            'ID': [1, 2, 2, 3], # Duplicate ID
            'Name': ['A', 'B', 'C', 'D']
        }
        self.create_dummy_excel(data_duplicate)
        validation_config_duplicate = {
            "check_unique_values": ["ID"]
        }
        validator_duplicate = ExcelValidator(self.dummy_filepath, validation_config_duplicate)
        self.assertTrue(validator_duplicate.load_excel())
        self.assertFalse(validator_duplicate.validate_data()) # Should fail
        report_duplicate = validator_duplicate.generate_report()
        self.assertIn("Overall Status: FAILED", report_duplicate)
        self.assertIn("Failed Rules:", report_duplicate)
        self.assertIn("- Rule 'check_unique_values' (Column: ID): Duplicate values found in column 'ID'.", report_duplicate)
        self.assertIn("- Rule 'load_excel' (status: passed)", report_duplicate)

        # Test case with a non-existent column in unique check config
        data_nonexistent = {
            'ID': [1, 2, 3]
        }
        self.create_dummy_excel(data_nonexistent)
        validation_config_nonexistent = {
            "check_unique_values": ["NonExistentColumn"]
        }
        validator_nonexistent = ExcelValidator(self.dummy_filepath, validation_config_nonexistent)
        self.assertTrue(validator_nonexistent.load_excel())
        self.assertTrue(validator_nonexistent.validate_data()) # Should pass (skipped)
        report_nonexistent = validator_nonexistent.generate_report()
        self.assertIn("Overall Status: PASSED", report_nonexistent)
        self.assertNotIn("Failed Rules:", report_nonexistent)
        self.assertIn("Skipped Rules:", report_nonexistent)
        self.assertIn("- Rule 'check_unique_values' (Column: NonExistentColumn): Column not found", report_nonexistent)
        self.assertIn("- Rule 'load_excel' (status: passed)", report_nonexistent)

    def test_generate_report_to_file(self):
        """Test generating the validation report to a file."""
        data = {
            'ID': [1, 2, '3'], # This will cause a type failure
            'Name': ['A', 'B', 'C']
        }
        self.create_dummy_excel(data)
        validation_config = {
            "column_types": {
                "ID": "int"
            }
        }
        validator = ExcelValidator(self.dummy_filepath, validation_config)
        self.assertTrue(validator.load_excel())
        self.assertFalse(validator.validate_data()) # Expecting validation failure

        # Generate report to a file
        report_filepath = self.report_filepath
        validator.generate_report(output_filepath=report_filepath)

        # Assert that the file was created
        self.assertTrue(os.path.exists(report_filepath))

        # Read the content of the file
        with open(report_filepath, 'r') as f:
            file_content = f.read()

        # Generate the same report as a string for comparison
        expected_report_content = validator.generate_report() # Call without filepath

        # Assert that the file content matches the expected report string
        self.assertEqual(file_content.strip(), expected_report_content.strip())

        # Check that the detailed_results list includes the report saving info
        report_save_result = next((res for res in validator.detailed_results if res["rule"] == "generate_report"), None)
        self.assertIsNotNone(report_save_result)
        self.assertEqual(report_save_result["status"], "info")
        self.assertIn(f"Report saved to {report_filepath}", report_save_result["details"])


# Run the tests
if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
