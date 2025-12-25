"""
Global configuration module for SW UT Report.

This module centralizes all configuration including:
- Jama connection settings
- Default values with search and replace applied
- Global state management
"""

import os
import logging
import re
from typing import Dict, Optional


class GlobalConfig:
    """
    Global configuration class that manages all application settings.

    This class centralizes configuration and applies search and replace
    for Jama ID prefixes once at startup.
    """

    # Class-level configuration storage
    _config: Optional[Dict[str, str]] = None
    _initialized: bool = False

    # Default values from environment variables
    JAMA_URL = os.getenv("JAMA_URL")
    JAMA_CLIENT_ID = os.getenv("JAMA_CLIENT_ID")
    JAMA_CLIENT_PASSWORD = os.getenv("JAMA_CLIENT_PASSWORD")
    JAMA_DEFAULT_PROJECT_ID = os.getenv("JAMA_DEFAULT_PROJECT_ID")
    JAMA_TEST_SET_ID = os.getenv("JAMA_TEST_SET_ID", "SmlPrep-SET-359")
    JAMA_UT_TEST_CASE_ID = os.getenv("JAMA_UT_TEST_CASE_ID", "SmlPrep-UT-1")
    JAMA_ID_PREFIX = os.getenv("JAMA_ID_PREFIX", "SmlPrep")
    JAMA_PREFIXES_TO_REPLACE = os.getenv("JAMA_PREFIXES_TO_REPLACE", "SmlPrep")

    @classmethod
    def _apply_jama_id_prefix_replacement(cls, value: str, jama_id_prefix: str = None) -> str:
        """
        Apply search and replace for Jama ID prefixes.

        Args:
            value: The value to process
            jama_id_prefix: The prefix to use for replacement (optional)

        Returns:
            str: The value with prefixes replaced
        """
        # Use provided prefix or default
        prefix_to_use = jama_id_prefix or cls.JAMA_ID_PREFIX

        # First, check if the value matches the pattern [LETTRES_MAJUSCULES]-[CHIFFRES]
        # This pattern must match the entire string (^...$)
        pattern = r'^[A-Z]+-[0-9]+$'
        if re.match(pattern, value):
            # Transform: ABC-123 + prefix → prefix-ABC-123
            return f"{prefix_to_use}-{value}"

        # If not matching the pattern, apply the existing search and replace logic
        # Get prefixes to replace from environment variable (comma-separated)
        prefixes_to_replace = [prefix.strip() for prefix in cls.JAMA_PREFIXES_TO_REPLACE.split(',') if prefix.strip()]

        # Apply replacements
        result = value
        for prefix in prefixes_to_replace:
            result = result.replace(prefix, prefix_to_use)

        return result

    @classmethod
    def initialize(cls,
                   project_id: Optional[str] = None,
                   test_set_id: Optional[str] = None,
                   ut_test_case_id: Optional[str] = None,
                   jama_id_prefix: Optional[str] = None) -> None:
        """
        Initialize the global configuration with CLI parameters.

        This method should be called once at startup after parsing CLI arguments.
        It applies search and replace to all default values.

        Args:
            project_id: CLI parameter for project ID
            test_set_id: CLI parameter for test set ID
            ut_test_case_id: CLI parameter for UT test case ID
            jama_id_prefix: CLI parameter for ID prefix replacement
        """
        # Use the provided jama_id_prefix or the default one
        current_prefix = jama_id_prefix or cls.JAMA_ID_PREFIX

        # Apply search and replace to default values if no CLI parameter is provided
        final_test_set_id = test_set_id or cls._apply_jama_id_prefix_replacement(cls.JAMA_TEST_SET_ID, current_prefix)
        final_ut_test_case_id = ut_test_case_id or cls._apply_jama_id_prefix_replacement(cls.JAMA_UT_TEST_CASE_ID, current_prefix)

        # Store the final configuration
        cls._config = {
            'project_id': project_id or cls.JAMA_DEFAULT_PROJECT_ID,
            'test_set_id': final_test_set_id,
            'ut_test_case_id': final_ut_test_case_id,
            'jama_id_prefix': current_prefix,
            'jama_url': cls.JAMA_URL,
            'jama_client_id': cls.JAMA_CLIENT_ID,
            'jama_client_password': cls.JAMA_CLIENT_PASSWORD,
        }

        cls._initialized = True

        logging.info("Global configuration initialized")
        logging.info(f"Config: project_id={cls._config['project_id']}, "
                    f"test_set_id={cls._config['test_set_id']}, "
                    f"ut_test_case_id={cls._config['ut_test_case_id']}, "
                    f"jama_id_prefix={cls._config['jama_id_prefix']}")

    @classmethod
    def get_config(cls) -> Dict[str, str]:
        """
        Get the current global configuration.

        Returns:
            Dict containing the configuration values

        Raises:
            RuntimeError: If configuration has not been initialized
        """
        if not cls._initialized or cls._config is None:
            raise RuntimeError("Global configuration has not been initialized. Call GlobalConfig.initialize() first.")

        return cls._config.copy()

    @classmethod
    def get(cls, key: str, default: str = None) -> str:
        """
        Get a specific configuration value.

        Args:
            key: The configuration key
            default: Default value if key not found

        Returns:
            str: The configuration value

        Raises:
            RuntimeError: If configuration has not been initialized
        """
        if not cls._initialized or cls._config is None:
            raise RuntimeError("Global configuration has not been initialized. Call GlobalConfig.initialize() first.")

        return cls._config.get(key, default)

    @classmethod
    def apply_jama_id_prefix_replacement(cls, text: str) -> str:
        """
        Apply search and replace for Jama ID prefixes to any text.

        This method uses the current global configuration.

        Args:
            text: The text to process

        Returns:
            str: The text with prefixes replaced
        """
        if not cls._initialized or cls._config is None:
            # Fallback to default if not initialized
            return cls._apply_jama_id_prefix_replacement(text)

        jama_id_prefix = cls._config.get('jama_id_prefix', cls.JAMA_ID_PREFIX)
        return cls._apply_jama_id_prefix_replacement(text, jama_id_prefix)

    @classmethod
    def is_initialized(cls) -> bool:
        """
        Check if the global configuration has been initialized.

        Returns:
            bool: True if initialized, False otherwise
        """
        return cls._initialized

    @classmethod
    def reset(cls) -> None:
        """
        Reset the global configuration. Useful for testing.
        """
        cls._config = None
        cls._initialized = False
        logging.info("Global configuration reset")


# Convenience functions for backward compatibility
def get_jama_config() -> Dict[str, str]:
    """
    Get Jama configuration from global config.

    Returns:
        Dict containing the configuration values
    """
    return GlobalConfig.get_config()


