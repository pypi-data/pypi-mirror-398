import unittest
import yaml
import tempfile
import pathlib
from unittest.mock import patch

import material_ai.ui_config as ui_config_loader
from material_ai.ui_config import get_ui_config, DEFAULT_CONFIG, UIConfig


class TestUIConfigLoader(unittest.TestCase):

    def setUp(self):
        """
        Resets the singleton instance before each test to ensure isolation.
        This is crucial because the config is designed to be loaded only once.
        """
        ui_config_loader._config_instance = None

    def test_get_config_with_no_file(self):
        """
        Test that DEFAULT_CONFIG is returned when no file path is provided.
        """
        config = get_ui_config(ui_config_yaml=None)
        self.assertEqual(config, DEFAULT_CONFIG)

    def test_config_caching(self):
        """
        Test that the configuration is loaded only once and subsequent calls
        return the cached instance.
        """
        # First call loads the config
        config1 = get_ui_config(ui_config_yaml=None)
        # Second call should return the exact same object from memory
        config2 = get_ui_config(ui_config_yaml=None)

        self.assertIs(
            config1, config2, "Config should be cached and return the same instance"
        )

    def test_get_config_with_valid_yaml(self):
        """
        Test loading a valid configuration from a YAML file.
        """
        custom_config_data = DEFAULT_CONFIG
        custom_config_data.title = "My Custom App"

        # Create a temporary YAML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
            yaml.dump(custom_config_data, tmp)
            tmp_path = tmp.name

        config = get_ui_config(ui_config_yaml=tmp_path)

        # Assert that the loaded config has the custom values
        self.assertIsInstance(config, UIConfig)
        self.assertEqual(config.title, "My Custom App")

        pathlib.Path(tmp_path).unlink()  # Clean up the temp file

    def test_get_config_file_not_found(self):
        """
        Test that DEFAULT_CONFIG is returned if the specified file does not exist.
        """
        non_existent_file = "non_existent_config.yaml"

        # Patch the logger to check if a warning was emitted
        with patch("material_ai.ui_config._logger.warning") as mock_log:
            config = get_ui_config(ui_config_yaml=non_existent_file)
            self.assertEqual(config, DEFAULT_CONFIG)
            mock_log.assert_called_once_with(
                f"WARNING: Config file not found at {pathlib.Path(non_existent_file)}"
            )

    def test_get_config_with_invalid_yaml_syntax(self):
        """
        Test fallback to DEFAULT_CONFIG when the YAML file has syntax errors.
        """
        invalid_yaml_content = "title: 'My App'\n  greeting: 'Hello'"  # Bad indentation

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
            tmp.write(invalid_yaml_content)
            tmp_path = tmp.name

        with patch("material_ai.ui_config._logger.warning") as mock_log:
            config = get_ui_config(ui_config_yaml=tmp_path)
            self.assertEqual(config, DEFAULT_CONFIG)
            # Check that a loading error was logged
            self.assertTrue(
                mock_log.call_args[0][0].startswith(
                    "WARNING: Error loading ui configuration"
                )
            )

        pathlib.Path(tmp_path).unlink()

    def test_get_config_with_schema_mismatch(self):
        """
        Test fallback to DEFAULT_CONFIG when YAML is valid but data doesn't
        match the Pydantic model (e.g., missing required 'title' field).
        """
        mismatched_data = {
            # "title": "This required field is missing",
            "greeting": "A greeting without a title",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
            yaml.dump(mismatched_data, tmp)
            tmp_path = tmp.name

        with patch("material_ai.ui_config._logger.warning") as mock_log:
            config = get_ui_config(ui_config_yaml=tmp_path)
            self.assertEqual(config, DEFAULT_CONFIG)

        pathlib.Path(tmp_path).unlink()


if __name__ == "__main__":
    unittest.main()
