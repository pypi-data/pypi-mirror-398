# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.config.settings.py
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

from __future__ import annotations
import logging
import os
import json

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

try:
    import whakerkit
    # Installed package
    WHAKERKIT = os.path.dirname(whakerkit.__file__) + "/"
except ImportError:
    # Development environment (local source)
    WHAKERKIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"

from .pathmanager import PathManager

# ---------------------------------------------------------------------------


class WhakerKitSettings:
    """Manage configuration settings for WhakerKit.

    This class handles loading settings from a configuration file and provides
    access to key attributes such as secret keys and additional configuration
    options.

    This class also defines default naming conventions and rules for folders
    and files, including separators, minimum name lengths, and invalid
    characters. Once initialized, the settings become immutable, enforcing
    consistency throughout the application. The class also supports context
    management, allowing temporary changes using the 'with' statement.
    These attributes are:

    - FOLDER_NAME_SEPARATOR (str): Character used to separate parts of a folder name.
    - FIELDS_NAME_SEPARATOR (str): Character used to separate fields within a folder name.
    - MIN_FILE_NAME_LENGTH (int): Minimum length required for a valid file name.
    - INVALID_CHARS_FOR_FOLDERS (str): String of characters that are disallowed in folder names.
    - INVALID_CHARS_FOR_FIELDS (str): String of characters that are disallowed in file names.
    - DOWNLOADS_FILENAME (str): Default name for the downloads file.
    - DESCRIPTION_FILENAME (str): Default name for the description file.

    :example:
    >>> with WhakerKitSettings() as settings:
    >>>     print(settings.name)
    "WhakerKit"
    >>>     settings.foo = 'bar'   # raise AttributeError
    >>>     del settings.name      # raise AttributeError

    """

    def __init__(self, config_filename: str | None = None, root_path : str | None = None):
        """Initialize the global application settings.

        Load the settings from the given configuration file. If the file or
        directory does not exist, necessary directories will be created.
        Attributes are frozen after initialization to prevent modification.

        Sets default values for folder and file name separators, as well as
        restrictions on file name lengths and characters. After initialization,
        the settings are frozen to prevent modifications unless explicitly
        unfrozen.

        :param config_filename: (str) Path to the configuration file.
        :param root_path: (str | os.PathLike): Project root.
            Converted to an absolute, normalised path.
        :raises: TypeError: if root_path is not a valid path or os.PathLike.

        """
        # Briefly allow to set attributes
        self._is_frozen = False

        # Load settings from a JSON configuration file or define default values.
        self.load(config_filename, root_path)

        # Check the existence of the documents upload directory
        if self.__pathman is None:
            uploads_dir = self.uploads
        else:
            uploads_dir = self.__pathman.get_root_path() + "/" + self.uploads
        logging.debug(f"Directory with documents: {uploads_dir}")
        if os.path.exists(uploads_dir) is False:
            logging.error(f"The directory with documents can't be accessed: {uploads_dir}")

        # Freeze the attribute for set and del.
        self._is_frozen = True

    # -----------------------------------------------------------------------

    def load(self, filename: str | None = None, root_path: str | None = None) -> None:
        """Load the dictionary of settings from a file or set default values.

        The configuration file must contain a JSON dictionary with the
        'WhakerKit' key holding the application's settings. If the file is
        missing, log an error and use default values for each required
        attribute.

        :param filename: (str) Path to the configuration file.
        :param root_path: (str | os.PathLike): Project root.
            Converted to an absolute, normalised path.
        :raises: TypeError: if root_path is not a valid path or os.PathLike.

        """
        # Load the JSON configuration file into "config" dictionary
        config = dict()
        if filename is not None:
            if os.path.exists(filename) is False:
                logging.warning("No such file or directory: {:s}".format(filename))
            else:
                with open(filename, encoding='utf-8') as cfg:
                    full_config = json.load(cfg)
                    if "WhakerKit" in full_config:
                        config = full_config["WhakerKit"]

        # Define the required global attributes in the class dictionary
        #   base_dir: dirname of this file
        #   path: relative path from the web server launcher path, to the 'whakerkit' folder.
        #   whakerexa: relative path from the web server launcher path, to wexa_statics
        #   uploads: relative path from the web server launcher path, to wexa_statics
        #   name: default name of the application
        #   secret_key: key for JWT
        #   jwt_validity: duration (in minutes) of the JWT token
        #   domain: domain name for LDAP
        #   lang: language to be used by the locale
        self.__dict__ = dict(
            base_dir=os.path.dirname(WHAKERKIT),
            path=WHAKERKIT,
            whakerexa=config.get("whakerexa", "./whakerexa/wexa_statics/"),
            uploads=config.get("uploads", "uploads"),
            name=config.get("name", "WhakerKitApp"),
            secret_key=config.get("secret_key", ""),
            jwt_validity=config.get("jwt_validity", "30"),
            domain=config.get("domain", None),
            lang=config.get("lang", "en"),

            # Separator used to separate the parts of a document folder name
            # and the one for the fields of a folder
            FOLDER_NAME_SEPARATOR='.',
            FIELDS_NAME_SEPARATOR='_',

            # Minimum length of a file name
            MIN_FILE_NAME_LENGTH=4,

            # Invalid characters for folder names
            INVALID_CHARS_FOR_FOLDERS="/\\.$@#%&*()[]{}<>:;,?\"'`!^+=|~",

            # Invalid characters for file names
            INVALID_CHARS_FOR_FIELDS="/$@#%&*()[]{}<>:;,?\"'`!^+=|~",

            # Default filenames
            DOWNLOADS_FILENAME="downloads.txt",
            DESCRIPTION_FILENAME="description.txt"
        )

        # Re-evaluate path. It should be relative.
        self.__pathman = None
        if root_path is not None:
            self.__pathman = PathManager(root_path)
            self.__dict__["path"] = self.__pathman.compute_relative_path(WHAKERKIT) + "/"

        # Folder with the shared documents: relative path from the web server launcher path
        # if os.path.exists(self.uploads) and filename is not None:
        #     self.__pathman = self.compute_root_path(WHAKERKIT, self.path)
        # else:
        #     # Default value for the absolute path of the project root
        #     self.__pathman = os.path.dirname(WHAKERKIT)

        # Append additional attributes defined in the config file
        if "addons" in config:
            for key in config["addons"]:
                if key not in self:
                    self.__dict__[key] = config["addons"][key]

    # -----------------------------------------------------------------------

    def get_root_path(self) -> str:
        """Return the absolute path of the hosting.

        If the abssolute path was not defined, it returns the absolute path
        of the WhakerKit root package.

        """
        if self.__pathman is None:
            return WHAKERKIT
        return self.__pathman.get_root_path()

    root_path = property(get_root_path, None, None)

    # -----------------------------------------------------------------------

    def set_lang(self, language: str):
        """Set the language of the application.

        Currently supported languages are 'fr' for French and 'en' for English.

        :param language: (str) The language of the application.
        :raises: ValueError: Invalid given language.

        """
        language = str(language).lower()
        if language not in ("fr", "en"):
            raise ValueError(f"Invalid language: {language}")

        self.unfreeze()
        self.__dict__['lang'] = str(language)
        self.freeze()

    # -----------------------------------------------------------------------

    def freeze(self):
        """Freeze the settings to make them immutable.

        Once frozen, any attempt to modify or delete attributes will raise
        an AttributeError.

        """
        super().__setattr__('_is_frozen', True)

    # -----------------------------------------------------------------------

    def unfreeze(self):
        """Unfreeze the settings, allowing temporary modifications.

         This allows attributes to be modified, but should be used with caution.

         """
        super().__setattr__('_is_frozen', False)

    # -----------------------------------------------------------------------
    # Overloads.
    # -----------------------------------------------------------------------

    def __setattr__(self, key: str, value):
        """Override to prevent setting attributes when frozen.

        If the settings are frozen, any attempt to set attributes will raise
        an AttributeError.

        :param key: (str) The attribute name.
        :param value: The value to be assigned to the attribute.
        :raises: AttributeError: if the settings are frozen.

        """
        if getattr(self, "_is_frozen", False):
            raise AttributeError(f"{self.__class__.__name__} object is immutable")
        super().__setattr__(key, value)

    # -----------------------------------------------------------------------

    def __delattr__(self, key):
        """Override to prevent deletion of attributes.

        All attempts to delete attributes will raise an AttributeError, whether
        the settings are frozen or not.

        :param key: (str) The attribute name.
        :raises: AttributeError: when attempting to delete an attribute.

        """
        raise AttributeError(f"{self.__class__.__name__} object does not allow attribute deletion")

    # -----------------------------------------------------------------------

    def __enter__(self):
        """Support 'with' context management.

        Allows the use of the `with` statement for managing configuration
        settings within a context block.

        :return: (WhakerKitSettings) The current settings instance.

        """
        return self

    # -----------------------------------------------------------------------

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the context block.

        This method is required for context management but does not perform any
        special operations upon exiting.

        """
        pass

    # -----------------------------------------------------------------------

    def __iter__(self):
        """Iterate over the class attributes.

        :return: (iterator) An iterator over the attribute names in the settings.

        """
        for item in self.__dict__.keys():
            yield item
