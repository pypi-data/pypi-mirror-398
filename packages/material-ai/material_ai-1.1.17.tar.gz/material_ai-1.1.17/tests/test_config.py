import unittest
import os
import threading
import tempfile
import configparser
from unittest.mock import patch
import pathlib
import material_ai.config as config_loader
from material_ai.config import ConfigError

# A sample valid config content for our tests
VALID_CONFIG_CONTENT = """
[SSO]
client_id = sso_client_id_from_file
client_secret = sso_client_secret_from_file
redirect_uri = http://localhost/redirect
session_secret_key = file_secret_key

[GENERAL]
debug = True

[ADK]
session_db_url = sqlite:///sessions.db

[GOOGLE]
genai_use_vertexai = False
api_key = google_api_key_from_file
"""


class TestConfigLoader(unittest.TestCase):

    def setUp(self):
        """Set up for each test."""
        # Reset the singleton instance before each test
        config_loader._config_instance = None
        # Keep a copy of the original environ to restore it later
        self.original_environ = os.environ.copy()

    def tearDown(self):
        """Clean up after each test."""
        os.environ.clear()
        os.environ.update(self.original_environ)
        config_loader._config_instance = None

    # --- Tests for get_config_value ---

    def test_get_config_value_env_var_precedence(self):
        """Environment variable should take precedence over the config file."""
        os.environ["TEST_PARAM"] = "env_value"
        parser = configparser.ConfigParser()
        parser.add_section("TEST")
        parser.set("TEST", "param", "file_value")

        value = config_loader.get_config_value(parser, "TEST", "param")
        self.assertEqual(value, "env_value")

    def test_get_config_value_from_file(self):
        """Value should be read from the config file if no env var is set."""
        parser = configparser.ConfigParser()
        parser.add_section("TEST")
        parser.set("TEST", "param", "file_value")

        value = config_loader.get_config_value(parser, "TEST", "param")
        self.assertEqual(value, "file_value")

    def test_get_config_value_with_default(self):
        """Default value should be used if no env var or file value exists."""
        parser = configparser.ConfigParser()
        parser.add_section("TEST")

        value = config_loader.get_config_value(
            parser, "TEST", "param", default="default_value"
        )
        self.assertEqual(value, "default_value")

    def test_get_config_value_required_missing_raises_error(self):
        """ConfigError should be raised for a required value that is not found."""
        parser = configparser.ConfigParser()
        parser.add_section("TEST")

        with self.assertRaises(ConfigError):
            config_loader.get_config_value(parser, "TEST", "param")

    # --- Tests for get_config ---

    def test_get_config_path_not_set_raises_error(self):
        """ConfigError should be raised if CONFIG_PATH environment variable is not set."""
        if "CONFIG_PATH" in os.environ:
            del os.environ["CONFIG_PATH"]
        with self.assertRaisesRegex(
            ConfigError, "Environment variable CONFIG_PATH not set"
        ):
            config_loader.get_config()

    def test_get_config_file_not_found_raises_error(self):
        """ConfigError should be raised if the config file does not exist."""
        os.environ["CONFIG_PATH"] = "non_existent_file.ini"
        with self.assertRaisesRegex(ConfigError, "Config file not found"):
            config_loader.get_config()

    def test_get_config_successful_load(self):
        """Should successfully load a valid configuration from a file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ini") as tmp:
            tmp.write(VALID_CONFIG_CONTENT)
            tmp_path = tmp.name

        os.environ["CONFIG_PATH"] = tmp_path

        # FIX: Ensure the environment variable is not set for this specific test
        # This isolates the test to only check file-loading logic.
        if "SSO_CLIENT_ID" in os.environ:
            del os.environ["SSO_CLIENT_ID"]
        if "GOOGLE_API_KEY" in os.environ:
            del os.environ["GOOGLE_API_KEY"]

        try:
            config_loader.get_config()  # This reloads the config
            config = config_loader._config_instance
            self.assertIsNotNone(config)
            self.assertEqual(config.sso.client_id, "sso_client_id_from_file")
            self.assertEqual(config.google.api_key, "google_api_key_from_file")
            self.assertTrue(config.general.debug)
        finally:
            os.remove(tmp_path)

    def test_get_config_singleton_behavior(self):
        """The configuration should only be loaded once."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ini") as tmp:
            tmp.write(VALID_CONFIG_CONTENT)
            tmp_path = tmp.name

        os.environ["CONFIG_PATH"] = tmp_path

        try:
            # First call should load the config
            config1 = config_loader.get_config()

            # Second call should return the same instance without reloading
            with patch.object(config_loader, "_configure") as mock_configure:
                config2 = config_loader.get_config()
                mock_configure.assert_not_called()
                self.assertIs(config1, config2)  # Check if it's the exact same object
        finally:
            os.remove(tmp_path)

    def test_get_config_env_var_override(self):
        """Values from environment variables should override file values."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ini") as tmp:
            tmp.write(VALID_CONFIG_CONTENT)
            tmp_path = tmp.name

        os.environ["CONFIG_PATH"] = tmp_path
        os.environ["SSO_CLIENT_ID"] = "sso_client_id_from_env"
        os.environ["GOOGLE_API_KEY"] = "google_api_key_from_env"

        try:
            config = config_loader.get_config()
            self.assertEqual(config.sso.client_id, "sso_client_id_from_env")
            self.assertEqual(config.google.api_key, "google_api_key_from_env")
        finally:
            os.remove(tmp_path)

    def test_thread_safety(self):
        """Ensure config is loaded only once in a multi-threaded environment."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ini") as tmp:
            tmp.write(VALID_CONFIG_CONTENT)
            tmp_path = tmp.name

        os.environ["CONFIG_PATH"] = tmp_path

        try:
            with patch.object(
                config_loader, "_configure", wraps=config_loader._configure
            ) as mock_configure:
                threads = []
                for _ in range(10):
                    thread = threading.Thread(target=config_loader.get_config)
                    threads.append(thread)
                    thread.start()

                for thread in threads:
                    thread.join()

                # _configure should only have been called exactly once
                self.assertEqual(mock_configure.call_count, 1)
        finally:
            os.remove(tmp_path)

    def test_get_config_invalid_content_raises_error(self):
        """
        Covers the generic 'except Exception' block in get_config.
        This is triggered when the file exists but its content is invalid,
        causing _configure to fail.
        """
        # Config content is missing the required [GENERAL] section
        invalid_config_content = """
        [SSO]
        client_id = test
        client_secret = test
        redirect_uri = http://localhost
        session_secret_key = test
        """
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ini") as tmp:
            tmp.write(invalid_config_content)
            tmp_path = tmp.name

        os.environ["CONFIG_PATH"] = tmp_path

        try:
            # We expect a ConfigError wrapping the original error
            with self.assertRaisesRegex(ConfigError, "Error loading configuration"):
                config_loader.get_config()
        finally:
            os.remove(tmp_path)

    def test_configure_with_directory_path_raises_error(self):
        """
        Covers the 'if not path.is_file()' check inside _configure.
        This requires calling the private function directly, as the public
        get_config() function already filters out directory paths.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = pathlib.Path(tmpdir)
            with self.assertRaises(FileNotFoundError):
                # We are testing the private _configure function in isolation here
                config_loader._configure(dir_path)


if __name__ == "__main__":
    unittest.main()
