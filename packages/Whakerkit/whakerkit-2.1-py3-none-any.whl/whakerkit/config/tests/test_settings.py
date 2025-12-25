"""
:filename: whakerkit.tests.test_settings.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The WhakerKit global settings, instantiated as 'sg'.

Copyright (C) 2024-2025 Brigitte Bigi, CNRS
Laboratoire Parole et Langage, Aix-en-Provence, France

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

This banner notice must not be removed.

"""

import os
import unittest
from unittest import mock

from whakerkit.config.settings import WhakerKitSettings


class TestSettings(unittest.TestCase):

    def setUp(self):
        self.all_settings = (
            "_WhakerKitSettings__root_path",
            "_WhakerKitSettings__pathman",
            "_is_frozen",
            "base_dir", "path", "whakerexa",
            "lang", "name",
            "uploads_path", "uploads",
            "secret_key", "domain",  "jwt_validity",
            'FOLDER_NAME_SEPARATOR', 'FIELDS_NAME_SEPARATOR',
            'MIN_FILE_NAME_LENGTH', 'INVALID_CHARS_FOR_FOLDERS',
            'INVALID_CHARS_FOR_FIELDS', 'DOWNLOADS_FILENAME',
            'DESCRIPTION_FILENAME'
        )
        self.config_file = os.path.join(os.path.dirname(__file__), "test_settings.json")
        self.invalid_config_file = os.path.join(os.path.dirname(__file__), "invalid_settings.json")

    # -----------------------------------------------------------------------

    def test_init(self):
        # Without settings configuration file
        settings = WhakerKitSettings()
        for key, value in settings.__dict__.items():
            self.assertIn(key, self.all_settings)

        # With a settings configuration file
        settings_with_file = WhakerKitSettings(config_filename=self.config_file)
        self.assertEqual(settings_with_file.name, "App")
        self.assertEqual(settings_with_file.domain, "some.dom")
        self.assertEqual(settings_with_file.jwt_validity, 420)
        self.assertEqual(settings_with_file.uploads, "sample/uploads")
        self.assertEqual(settings_with_file.whakerexa, "./whakerexa/wexa_statics/")
        # Path is absolute if no root is given
        self.assertTrue(settings_with_file.path.endswith("whakerkit/"))

        # With root_path
        settings = WhakerKitSettings(
            config_filename=None,
            root_path=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.assertEqual("..", settings.path)
        settings = WhakerKitSettings(
            config_filename=None,
            root_path=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.assertEqual(".", settings.path)
        settings = WhakerKitSettings(
            config_filename=None,
            root_path=os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        self.assertEqual("whakerkit", settings.path)

    # -----------------------------------------------------------------------

    def test_enter(self):
        with WhakerKitSettings() as settings:
            for key, value in settings.__dict__.items():
                self.assertIn(key, self.all_settings)
        with WhakerKitSettings(config_filename=self.config_file) as settings_with_file:
            self.assertEqual(settings_with_file.name, "App")
            self.assertEqual(settings_with_file.secret_key, "")
            self.assertEqual(settings_with_file.domain, "some.dom")

    # -----------------------------------------------------------------------

    def test_attr(self):
        # WhakerKitSettings object is immutable by default
        with WhakerKitSettings() as settings:
            # Can't modify an existing attribute
            with self.assertRaises(AttributeError):
                settings.FOLDER_NAME_SEPARATOR = "."

            # Can't delete an existing attribute
            with self.assertRaises(AttributeError):
                del settings.FOLDER_NAME_SEPARATOR

            # Can't add a new attribute
            with self.assertRaises(AttributeError):
                settings.MAX_FILE_NAME_LENGTH = 256

        # WhakerKitSettings object can be turned into a mutable object
        with WhakerKitSettings() as settings:
            settings.unfreeze()

            # Can add a new attribute
            settings.new_attribute = "-"
            self.assertEqual(settings.new_attribute, "-")

            # Can modify an existing attribute
            settings.name = "Terminator"
            self.assertEqual(settings.name, "Terminator")

            # Still can't delete an existing attribute
            with self.assertRaises(AttributeError):
                del settings.name

    # -----------------------------------------------------------------------

    def test_load_addons(self):
        """Test loading additional attributes (addons) from the configuration file."""
        settings_with_file = WhakerKitSettings(config_filename=self.config_file)

        # Verify the "addons" key exists in the config and attributes are set correctly
        self.assertTrue(hasattr(settings_with_file, "some_key"))
        self.assertEqual(settings_with_file.some_key, True)

    # -----------------------------------------------------------------------

    def test_secret_key_empty(self):
        """Test that the secret_key is empty as specified in the test configuration file."""
        settings_with_file = WhakerKitSettings(config_filename=self.config_file)
        self.assertEqual(settings_with_file.secret_key, "")

    # -----------------------------------------------------------------------

    def test_lang(self):
        """Test assigning a different language."""
        settings_with_file = WhakerKitSettings(config_filename=self.config_file)
        self.assertEqual(settings_with_file.lang, "en")

        # Can't use '=' to set any variable, including 'lang'
        with self.assertRaises(AttributeError):
            settings_with_file.lang = "fr"

        # Can use set_lang() to change language
        settings_with_file.set_lang("fr")
        self.assertEqual(settings_with_file.lang, "fr")

        # Can't assign an non-supported language
        with self.assertRaises(ValueError):
            settings_with_file.set_lang("de")

    # -----------------------------------------------------------------------

    @mock.patch('whakerkit.config.settings.logging.error')  # Mock logger
    def test_invalid_config_file(self, mock_log_error):
        """Test with an invalid or nonexistent configuration file."""
        # This should not raise an exception but should log an error and use default values
        settings_with_invalid_file = WhakerKitSettings(config_filename=self.invalid_config_file)

        # Check that settings fall back to default values
        self.assertEqual(settings_with_invalid_file.name, "WhakerKitApp")  # Default value
        self.assertIsNone(settings_with_invalid_file.domain)               # Default value is None
        self.assertEqual(settings_with_invalid_file.jwt_validity, "30")    # Default value

        # Log message should indicate the file was not found
        self.assertEqual(settings_with_invalid_file.uploads, "uploads")
        mock_log_error.assert_called_once_with(f"No such file or directory: {self.invalid_config_file}")
