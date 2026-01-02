"""
regexapp.config
===============
Core attributes and metadata for the regexapp package.

This module defines application-level constants, metadata, and helper
utilities for managing references, dependencies, and configuration
files used by regexapp. It centralizes versioning, edition information,
company details, and file paths for system and user reference data.

Contents
--------
- Version and edition identifiers (`version`, `edition`).
- The `Data` class, which encapsulates:
  * File paths for system references, symbols, and user keyword files.
  * Application metadata such as version, company information, and URLs.
  * Package dependency details (PyYAML, genericlib).
  * License information and copyright text.
  * Class methods for retrieving reference content and user-defined
    keywords.

Notes
-----
- Reference files are expected to be YAML documents located in the
  package directory or user home directory.
- User keyword files are automatically created and initialized with
  sample content if missing.
- License text is read from the `LICENSE` file at module import time.
"""

from os import path

from pathlib import Path
from pathlib import PurePath

import yaml

from genericlib import version as gtlib_version
from genericlib import File

import regexapp.utils as utils

__version__ = '0.5.1a2'
version = __version__
__edition__ = 'Community'
edition = __edition__

__all__ = [
    'version',
    'edition',
    'Data'
]


class Data:
    """
    Centralized application metadata and reference management for regexapp.

    The `Data` class encapsulates constants, metadata, and helper methods
    used throughout the regexapp application. It provides access to
    versioning information, company details, repository URLs, license
    text, and file paths for system and user reference data. It also
    includes utilities for retrieving dependency information and loading
    keyword or symbol definitions from YAML files.

    Attributes
    ----------
    system_reference_filename : str
        Path to the YAML file containing system-level keyword references.
    symbol_reference_filename : str
        Path to the YAML file containing symbol definitions.
    sample_user_keywords_filename : str
        Path to the sample YAML file used to initialize user keyword data.
    user_reference_filename : str
        Path to the YAML file containing user-defined keyword references,
        located in the user's home directory.
    app_version : str
        Current application version string.
    main_app_text : str
        Human-readable application name and version.
    pyyaml_text : str
        Version string for the PyYAML dependency.
    pyyaml_link : str
        URL to the PyYAML package documentation.
    gtgenlib_text : str
        Version string for the genericlib dependency.
    gtgenlib_link : str
        URL to the genericlib package documentation.
    company : str
        Legal company name.
    company_full_name : str
        Full company name string.
    company_name : str
        Shortened company name.
    company_url : str
        Official company website URL.
    repo_url : str
        URL to the regexapp GitHub repository.
    documentation_url : str
        URL to the regexapp README documentation.
    license_url : str
        URL to the regexapp license file.
    years : str
        Copyright year(s).
    license_name : str
        License name string.
    copyright_text : str
        Copyright notice string.
    license : str
        Full license text loaded from the LICENSE file.

    Methods
    -------
    get_dependency() -> dict
        Return a dictionary of package dependencies and their URLs.
    get_app_keywords() -> str
        Load and return the contents of the system reference YAML file.
    get_defined_symbols() -> str
        Load and return the contents of the symbol reference YAML file.
    get_user_custom_keywords() -> str
        Load and return the contents of the user keyword YAML file.
        If the file does not exist, it is created and initialized with
        sample content.

    Notes
    -----
    - Reference files are expected to be YAML documents located in the
      package directory or user home directory.
    - User keyword files are automatically created and initialized with
      sample content if missing.
    - License text is read from the `LICENSE` file at module import time.
    - This class provides static metadata and helper methods; it is not
      intended to be instantiated.
    """

    # app yaml files
    system_reference_filename = str(
        PurePath(
            Path(__file__).parent,
            'system_references.yaml'
        )
    )
    symbol_reference_filename = str(
        PurePath(
            Path(__file__).parent,
            'symbols.yaml'
        )
    )
    sample_user_keywords_filename = str(
        PurePath(
            Path(__file__).parent,
            'sample_user_keywords.yaml'
        )
    )
    user_reference_filename = str(
        PurePath(
            Path.home(),
            '.geekstrident',
            'regexapp',
            'user_references.yaml'
        )
    )

    app_version = version

    # main app
    main_app_text = f'RegexApp v{version}'

    # packages
    pyyaml_text = f'pyyaml v{yaml.__version__}'
    pyyaml_link = 'https://pypi.org/project/PyYAML/'

    gtgenlib_text = f"genericlib v{gtlib_version}"
    gtgenlib_link = "https://pypi.org/project/genericlib/"

    # company
    company = 'Geeks Trident LLC'
    company_full_name = company
    company_name = "Geeks Trident"
    company_url = 'https://www.geekstrident.com/'

    # URL
    repo_url = 'https://github.com/Geeks-Trident-LLC/regexapp'
    documentation_url = path.join(repo_url, 'blob/develop/README.md')
    license_url = path.join(repo_url, 'blob/develop/LICENSE')

    # License
    years = '2022'
    license_name = f'{company_name} License'
    copyright_text = f'Copyright \xa9 {years}'
    license = utils.File.read('LICENSE')

    @classmethod
    def get_dependency(cls):
        """
        Retrieve package dependency information for regexapp.

        This method returns a dictionary containing metadata about
        external packages required by regexapp. Each dependency entry
        includes the package name and version string, along with a
        reference URL to its documentation or distribution source.

        Returns
        -------
        dict
            A dictionary of dependency metadata with the following keys:
            - ``pyyaml`` : dict
                Information about the PyYAML package, including version
                string and PyPI URL.
            - ``gtgenlib`` : dict
                Information about the genericlib package, including version
                string and PyPI URL.

        Notes
        -----
        - Dependency information is derived from class-level attributes
          initialized at module import time.
        - This method does not verify installation status; it only reports
          metadata defined in the `Data` class.
        """
        dependencies = dict(
            pyyaml=dict(
                package=cls.pyyaml_text,
                url=cls.pyyaml_link
            ),
            gtgenlib=dict(
                package=cls.gtgenlib_text,
                url=cls.gtgenlib_link
            )
        )
        return dependencies

    @classmethod
    def get_app_keywords(cls):
        """
        Load and return system-level keyword definitions for regexapp.

        This method reads the contents of the system reference YAML file
        defined by `Data.system_reference_filename`. The file contains
        application-wide keyword definitions used by regexapp for test
        generation, validation, and configuration.

        Returns
        -------
        str
            A string containing the raw contents of the system reference
            YAML file.

        Notes
        -----
        - The returned value is the raw file content, not a parsed Python
          object. Use `yaml.safe_load` or similar functions to parse the
          YAML content if structured access is required.
        - The system reference file is expected to exist in the package
          directory and be maintained as part of regexapp’s configuration.
        - This method does not perform validation of the YAML structure;
          it only returns the file contents as text.
        """
        content = utils.File.read(Data.system_reference_filename)
        return content

    @classmethod
    def get_defined_symbols(cls):
        """
        Load and return symbol definitions for regexapp.

        This method reads the contents of the symbol reference YAML file
        defined by `Data.symbol_reference_filename`. The file contains
        symbol definitions used by regexapp for test generation, validation,
        and configuration.

        Returns
        -------
        str
            A string containing the raw contents of the symbol reference
            YAML file.

        Notes
        -----
        - The returned value is the raw file content, not a parsed Python
          object. Use `yaml.safe_load` or similar functions to parse the
          YAML content if structured access is required.
        - The symbol reference file is expected to exist in the package
          directory and be maintained as part of regexapp’s configuration.
        - This method does not perform validation of the YAML structure;
          it only returns the file contents as text.
        """
        content = utils.File.read(Data.symbol_reference_filename)
        return content

    @classmethod
    def get_user_custom_keywords(cls):
        """
        Load and return user-defined keyword definitions for regexapp.

        This method reads the contents of the user reference YAML file
        defined by `Data.user_reference_filename`. If the file does not
        exist, it is automatically created and initialized with sample
        keyword content from `Data.sample_user_keywords_filename`. The
        returned content provides user-specific keyword definitions that
        can be used for test generation, validation, and configuration.

        Returns
        -------
        str
            A string containing the raw contents of the user reference
            YAML file.

        Notes
        -----
        - The returned value is the raw file content, not a parsed Python
          object. Use `yaml.safe_load` or similar functions to parse the
          YAML content if structured access is required.
        - If the user reference file does not exist, it is created in the
          user's home directory under `.geekstrident/regexapp/`.
        - The file is initialized with sample keyword definitions copied
          from `sample_user_keywords.yaml`.
        - This method does not perform validation of the YAML structure;
          it only returns the file contents as text.
        """

        filename = cls.user_reference_filename
        sample_file = cls.sample_user_keywords_filename
        if not File.is_exist(filename):
            File.create(filename)
            File.copy_file(sample_file, filename)

        content = utils.File.read(filename)
        return content
