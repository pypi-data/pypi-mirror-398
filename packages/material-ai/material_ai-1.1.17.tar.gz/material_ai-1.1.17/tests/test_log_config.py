import unittest
import logging
import json
from io import StringIO
import sys
from datetime import datetime, timezone

# Assuming the file to be tested is in the same directory and named log_config.py
from material_ai.log_config import (
    setup_structured_logging,
    AppNameFilter,
    JsonFormatter,
)


class TestLoggingConfig(unittest.TestCase):
    """
    Unit tests for the structured logging configuration.
    """

    def setUp(self):
        """
        Set up for each test. Redirects stdout to capture log output
        and resets the logging configuration.
        """
        # Reset logging handlers to ensure a clean state for each test
        root_logger = logging.getLogger()
        root_logger.handlers = []
        root_logger.setLevel(logging.WARNING)  # Reset to default level

        # Redirect stdout to capture logs
        self.log_capture_string = StringIO()
        self.original_stdout = sys.stdout
        sys.stdout = self.log_capture_string

    def tearDown(self):
        """
        Clean up after each test. Restores stdout and resets logging.
        """
        sys.stdout = self.original_stdout
        # It's good practice to reset logging again after tests
        root_logger = logging.getLogger()
        root_logger.handlers = []
        root_logger.setLevel(logging.WARNING)

    def test_app_name_filter(self):
        """
        Tests that the AppNameFilter correctly adds the appname to a log record.
        """
        test_app_name = "my-test-app"
        log_filter = AppNameFilter(appname=test_app_name)
        record = logging.LogRecord(
            "test_logger", logging.INFO, "/path/to/file", 10, "Test message", (), None
        )

        self.assertTrue(log_filter.filter(record))
        self.assertEqual(record.appname, test_app_name)

    def test_json_formatter_time_format(self):
        """
        Tests that the JsonFormatter formats the time in RFC 3339 format.
        """
        formatter = JsonFormatter()
        now = datetime.now(timezone.utc)
        record = logging.LogRecord(
            "test_logger", logging.INFO, "/path/to/file", 10, "Test message", (), None
        )
        record.created = now.timestamp()  # Set a specific time

        formatted_time = formatter.formatTime(record)
        # Check if the output is a valid ISO 8601 format string ending with 'Z'
        self.assertTrue(formatted_time.endswith("Z"))
        # Check if we can parse it back
        parsed_time = datetime.fromisoformat(
            formatted_time[:-1]
        )  # Remove 'Z' for parsing
        self.assertAlmostEqual(parsed_time.timestamp(), now.timestamp(), places=3)

    def test_setup_structured_logging_default_format(self):
        """
        Tests the default (non-JSON) logging format.
        """
        app_name = "default-app"
        setup_structured_logging(app_name=app_name, enable_json_formatter=False)

        logger = logging.getLogger("test_default_logger")
        logger.setLevel(logging.INFO)
        test_message = "This is a standard log."
        logger.info(test_message)

        log_output = self.log_capture_string.getvalue().strip()

        # Example output: test_default_logger INFO This is a standard log.
        self.assertIn("INFO", log_output)
        self.assertIn(test_message, log_output)
        self.assertNotIn('"severity":', log_output)  # Should not be JSON

    def test_setup_structured_logging_json_format(self):
        """
        Tests that JSON formatting is correctly applied when enabled.
        """
        app_name = "json-app"
        setup_structured_logging(app_name=app_name, enable_json_formatter=True)

        logger = logging.getLogger("test_json_logger")
        logger.setLevel(logging.INFO)
        test_message = "This is a JSON log."
        logger.info(test_message)

        log_output = self.log_capture_string.getvalue().strip()

        # The output should be a valid JSON string
        try:
            log_data = json.loads(log_output)
        except json.JSONDecodeError:
            self.fail("Log output is not valid JSON.")

        self.assertEqual(log_data["severity"], "INFO")
        self.assertEqual(log_data["appname"], app_name)
        self.assertEqual(log_data["message"], test_message)
        self.assertIn("timestamp", log_data)

    def test_log_level_setting(self):
        """
        Tests that the log level is correctly set by the setup function.
        """
        setup_structured_logging(log_level=logging.WARNING)

        logger = logging.getLogger("test_level_logger")

        logger.info("This INFO message should NOT be logged.")
        logger.warning("This WARNING message should be logged.")

        log_output = self.log_capture_string.getvalue().strip()

        self.assertNotIn("This INFO message", log_output)
        self.assertIn("This WARNING message", log_output)

    def test_log_level_setting(self):
        """
        Tests that the log level is correctly set by the setup function.
        """
        setup_structured_logging(log_level=logging.DEBUG)

        logger = logging.getLogger("test_level_logger")

        logger.info("This INFO message should NOT be logged.")
        logger.warning("This WARNING message should be logged.")

        log_output = self.log_capture_string.getvalue().strip()

        self.assertIn("This INFO message", log_output)
        self.assertIn("This WARNING message", log_output)

    def test_no_app_name(self):
        """
        Tests behavior when no app_name is provided. It should be None.
        """
        setup_structured_logging(app_name=None, enable_json_formatter=True)

        logger = logging.getLogger("test_no_app_name_logger")
        logger.setLevel(logging.INFO)
        test_message = "Log without an app name."
        logger.info(test_message)

        log_output = self.log_capture_string.getvalue().strip()
        log_data = json.loads(log_output)

        self.assertIsNone(log_data["appname"])


if __name__ == "__main__":
    unittest.main()
