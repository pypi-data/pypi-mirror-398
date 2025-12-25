"""
Common module for Jama integration utilities for Unit Test management.
This module provides shared functionality for connecting to Jama and managing UT operations.
"""

import json
import logging
import os
import re
import sys
import traceback
from typing import Dict, List, Optional
import difflib

from dotenv import load_dotenv
from py_jama_rest_client.client import APIException, JamaClient
from .config import GlobalConfig

load_dotenv()

# Jama configuration is now managed by GlobalConfig

# Constants for Jama item types and relationship types
ITEM_TYPES = {
    'FOLDER': 32,
    'UNIT_TEST': 167,
    'TEST_PLAN': 35,
    'TEST_CYCLE': 36,
    'TEST_RUN': 37
}

# Relationship types (based on your Jama configuration)
RELATIONSHIP_TYPES = {
    'VERIFICATION': 16,   # As specified in your original request
    'RELATED_TO': None,   # Default - don't specify type, let Jama use default
}

# Workflow status constants
WORKFLOW_STATUS_FIELD = 'workflow_status$167'  # Jama field name for workflow status (from item type fields)
WORKFLOW_STATUS_ACCEPTED = 'Accepted'     # Target status for unit tests

# Workflow status numeric values based on pick list configuration
WORKFLOW_STATUS_IDS = {
    'Draft': 639,
    'Review': 640,
    'Accepted': 641,
    'Rework': 642,
    'Deferred': 643,
    'Obsolete': 644,
    'Admin': 645
}

def get_status_name_from_id(status_id):
    """
    Get the status name from numeric ID for logging purposes.

    Args:
        status_id: Numeric status ID

    Returns:
        str: Status name or 'Unknown' if not found
    """
    for name, id_value in WORKFLOW_STATUS_IDS.items():
        if id_value == status_id:
            return name
    return f'Unknown({status_id})'

def determine_relationship_type_for_unit_test(req_item: Dict) -> Optional[int]:
    """
    Determine the appropriate relationship type for a requirement -> Unit Test relationship
    based on the relationship tables and item type.

    Args:
        req_item: The requirement item from Jama

    Returns:
        int or None: Relationship type ID, or None to use default
    """
    # Get item type information
    req_item_type = req_item.get('itemType')
    req_type_name = req_item.get('fields', {}).get('itemType', '').upper()

    # Alternative: check document key pattern for type identification
    doc_key = req_item.get('documentKey', '').upper()

    logging.info(f"Determining relationship type for item type: {req_item_type}, name: {req_type_name}, doc_key: {doc_key}")

    # Based on relationship tables:
    # Subsystem Requirement -> Unit Test = Verification
    if ('SUBSR' in req_type_name or 'SUBSYSTEM' in req_type_name or
        'SUBSR' in doc_key or any(pattern in doc_key for pattern in ['SUBSR', 'SUB-'])):
        logging.info("Detected Subsystem Requirement - using Verification relationship")
        return RELATIONSHIP_TYPES['VERIFICATION']

    # SW Item Design -> Unit Test = Related to (use default)
    elif ('SW' in req_type_name and 'ITEM' in req_type_name) or 'SWID' in doc_key:
        logging.info("Detected SW Item Design - using default relationship type")
        return RELATIONSHIP_TYPES['RELATED_TO']  # None = use default

    # System Requirement -> Unit Test = Verification (implied from tables)
    elif ('SYSTEM' in req_type_name or 'SYS' in req_type_name or
          any(pattern in doc_key for pattern in ['SYS-', 'SYSREQ', 'SYSTEM'])):
        logging.info("Detected System Requirement - using Verification relationship")
        return RELATIONSHIP_TYPES['VERIFICATION']

    # Test Plan -> Unit Test = Related to (use default)
    elif 'TEST' in req_type_name and 'PLAN' in req_type_name:
        logging.info("Detected Test Plan - using default relationship type")
        return RELATIONSHIP_TYPES['RELATED_TO']  # None = use default

    # Default case: use verification for safety (covers most requirement types)
    else:
        logging.info(f"Unknown item type - using Verification relationship as default")
        return RELATIONSHIP_TYPES['VERIFICATION']


class JamaConnectionError(Exception):
    """Custom exception for Jama connection and API issues."""
    pass


class JamaValidationError(Exception):
    """Custom exception for Jama business logic validation errors."""
    pass


class JamaItemNotFoundError(JamaValidationError):
    """Custom exception for when a specific Jama item is not found."""
    pass


class JamaRequiredItemNotFoundError(JamaValidationError):
    """Custom exception for when a required Jama item (like the configured test set) is not found."""
    pass


class JamaUTManager:
    """
    Manager class for Jama Unit Test operations.
    Handles UT creation, folder management, and relationship establishment.
    Implemented as a singleton with global configuration management.
    """

    _instance: Optional['JamaUTManager'] = None

    def __new__(cls, project_id: Optional[str] = None, test_set_id: Optional[str] = None, ut_test_case_id: Optional[str] = None):
        """Singleton pattern implementation - only one instance allowed."""
        # Strict validation: prevent direct instantiation with parameters
        if project_id is not None or test_set_id is not None or ut_test_case_id is not None:
            raise ValueError(
                "JamaUTManager must be instantiated using get_instance() method. "
                "Direct instantiation with parameters is not allowed. "
                "Use JamaUTManager.update_global_config() to set configuration at startup."
            )

        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, project_id: Optional[str] = None, test_set_id: Optional[str] = None, ut_test_case_id: Optional[str] = None):
        """Initialize the JamaUTManager with global configuration."""
        # Prevent re-initialization if already initialized
        if hasattr(self, '_initialized'):
            return

        self.jama_client: Optional[JamaClient] = None

        # Use global configuration
        if not GlobalConfig.is_initialized():
            raise RuntimeError("Global configuration has not been initialized. Call JamaUTManager.update_global_config() first.")

        config = GlobalConfig.get_config()
        logging.info("Using global configuration for JamaUTManager")

        logging.info(f"DEBUG: jama_project_id = {config['project_id']}")
        logging.info(f"DEBUG: jama_test_set_id = {config['test_set_id']}")
        logging.info(f"DEBUG: jama_ut_test_case_id = {config['ut_test_case_id']}")

        self.project_id = int(config['project_id']) if config['project_id'] else None
        self.test_set_id = config['test_set_id']
        self.ut_test_case_id = config['ut_test_case_id']
        self.jama_id_prefix = config['jama_id_prefix']

        # Cache for module folder children to avoid repeated API calls
        self._module_children_cache: Dict[int, List[Dict]] = {}

        # Validate required environment variables
        if not all([config['jama_url'], config['jama_client_id'], config['jama_client_password'], config['project_id']]):
            raise JamaConnectionError("Jama environment variables are not properly set")

        self._initialized = True

    @classmethod
    def update_global_config(cls, project_id: Optional[str] = None, test_set_id: Optional[str] = None, ut_test_case_id: Optional[str] = None, jama_id_prefix: Optional[str] = None) -> None:
        """
        Update global configuration for all future JamaUTManager instances.
        This should be called once at startup after parsing CLI arguments.

        Args:
            project_id: CLI parameter for project ID
            test_set_id: CLI parameter for test set ID
            ut_test_case_id: CLI parameter for UT test case ID
            jama_id_prefix: CLI parameter for ID prefix replacement
        """
        # Initialize the global configuration
        GlobalConfig.initialize(project_id, test_set_id, ut_test_case_id, jama_id_prefix)
        logging.info("Global JamaUTManager configuration updated")

    @classmethod
    def get_instance(cls) -> 'JamaUTManager':
        """
        Get the singleton instance. Creates it if it doesn't exist.

        Returns:
            JamaUTManager: The singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance. Useful for testing.
        """
        cls._instance = None
        GlobalConfig.reset()

    def _normalize_jama_url(self, url: str) -> str:
        """
        Normalize Jama URL to full Jama Cloud URL format.

        Args:
            url: The raw URL from environment variable

        Returns:
            str: Normalized URL in Jama Cloud format
        """
        if not url:
            return url

        # Check if URL is already a full URL
        if url.startswith(('http://', 'https://')):
            return url

        # Check if it already has .jamacloud.com
        if '.jamacloud.com' in url:
            normalized_url = f"https://{url}" if not url.startswith('https://') else url
        else:
            normalized_url = f"https://{url}.jamacloud.com"

        logging.info(f"Normalized Jama URL: {url} -> {normalized_url}")
        return normalized_url

    def init_jama_client(self) -> JamaClient:
        """
        Initialize the Jama client with OAuth authentication.

        Returns:
            JamaClient: Initialized Jama client

        Raises:
            JamaConnectionError: If client initialization fails
        """
        try:
            config = GlobalConfig.get_config()
            normalized_url = self._normalize_jama_url(config['jama_url'])

            self.jama_client = JamaClient(
                normalized_url,
                credentials=(config['jama_client_id'], config['jama_client_password']),
                oauth=True
            )
            logging.info("Jama UT client initialized successfully")
            return self.jama_client
        except APIException as e:
            logging.exception(f"Failed to initialize Jama client: {e}")
            raise JamaConnectionError(f"Failed to initialize Jama client: {e}")

    def get_client(self) -> JamaClient:
        """
        Get the Jama client, initializing if necessary.

        Returns:
            JamaClient: The Jama client instance
        """
        if self.jama_client is None:
            self.init_jama_client()
        return self.jama_client

    def get_item_by_document_key(self, document_key: str, item_type: int = None) -> Optional[Dict]:
        """
        Retrieve an item from Jama by its document key using efficient search.
        If item_type is provided, only return if the item matches the type.

        Args:
            document_key: The document key to search for
            item_type: Optional Jama item type ID to filter (e.g., ITEM_TYPES['UNIT_TEST'])

        Returns:
            Dict or None: The item if found, None otherwise

        Raises:
            JamaConnectionError: If API connection fails
            JamaItemNotFoundError: If item is not found (business validation)
        """
        try:
            client = self.get_client()
            search_results = client.get_abstract_items(
                project=self.project_id,
                contains=[document_key]
            )
            for item in search_results:
                if item.get('documentKey') == document_key:
                    if item_type is None or item.get('itemType') == item_type:
                        return item
            return None
        except APIException as e:
            logging.error(f"Error retrieving item with document key '{document_key}': {e}")
            raise JamaConnectionError(f"Error retrieving item '{document_key}': {e}")
        except Exception as e:
            logging.error(f"Error retrieving item by document key '{document_key}': {e}")
            return None

    def validate_test_set_exists(self) -> Dict:
        """
        Validate that the configured test set ID exists and is accessible using efficient search.
        This is the actual parent container where module folders are created.

        Returns:
            Dict: The test set item data

        Raises:
            JamaConnectionError: If API connection fails
            JamaRequiredItemNotFoundError: If the test set doesn't exist
        """
        try:
            # Use efficient search for the configured test set ID
            client = self.get_client()
            search_results = client.get_abstract_items(
                project=self.project_id,
                contains=[self.test_set_id]
            )

            # Look for exact match
            for item in search_results:
                if item.get('documentKey') == self.test_set_id:
                    logging.info(f"Found {self.test_set_id}: {item['fields']['name']}")
                    return item

            raise JamaRequiredItemNotFoundError(f"{self.test_set_id} not found - cannot proceed with UT creation")
        except APIException as e:
            logging.error(f"Error validating {self.test_set_id}: {e}")
            raise JamaRequiredItemNotFoundError(f"{self.test_set_id} not found - cannot proceed with UT creation")

    def get_children_items(self, parent_id: int) -> Optional[List[Dict]]:
        """
        Get direct children of an item using REST API call with pagination support.
        Uses caching to avoid repeated API calls for the same parent.

        Args:
            parent_id: ID of the parent item

        Returns:
            List[Dict] or None: List of child items, or None if API call failed
        """
        # Check cache first
        if parent_id in self._module_children_cache:
            logging.info(f"Using cached children for parent {parent_id} ({len(self._module_children_cache[parent_id])} items)")
            return self._module_children_cache[parent_id]

        try:
            client = self.get_client()
            # Access the underlying HTTP client like in IT integration code
            core = client._JamaClient__core

            all_children = []
            start_at = 0
            max_results = 50  # Jama's maximum per page

            while True:
                # Debug: Show the URL being called
                url = f"items/{parent_id}/children?startAt={start_at}&maxResults={max_results}"
                logging.debug(f"Calling REST API: GET {url}")

                response = core.get(url)

                logging.debug(f"Response status: {response.status_code}")

                if response.status_code == 200:
                    children_data = response.json()
                    logging.debug(f"Response keys: {list(children_data.keys())}")

                    data = children_data.get('data', [])
                    logging.debug(f"Data contains {len(data)} items")

                    # Debug: Show first few items if any
                    if data:
                        for i, item in enumerate(data[:3]):  # Show first 3 items
                            logging.debug(f"Item {i+1}: {item}")

                    all_children.extend(data)

                    # If we got fewer items than max_results, we've reached the end
                    if len(data) < max_results:
                        logging.debug(f"Reached end of children (got {len(data)} < {max_results})")
                        break

                    start_at += max_results
                else:
                    logging.debug(f"Response text: {response.text}")
                    logging.error(f"Failed to get children for item {parent_id}: {response.status_code} - {response.text}")
                    return None  # Return None to indicate API failure

            logging.debug(f"Total children retrieved: {len(all_children)}")

            # Cache the results for future use
            self._module_children_cache[parent_id] = all_children
            logging.info(f"Cached children for parent {parent_id} ({len(all_children)} items)")

            return all_children

        except Exception as e:
            logging.error(f"Error getting children for item {parent_id} via REST API: {e}")
            logging.debug(f"Exception details: {e}")
            logging.debug(f"Full traceback: {traceback.format_exc()}")
            return None  # Return None to indicate API failure

    def get_children_items_by_location(self, parent_id: int) -> List[Dict]:
        """
        Get items under a parent using abstractitems search with location filtering.
        This is more reliable than the children endpoint for some Jama configurations.
        Implements pagination to get all items.

        Args:
            parent_id: ID of the parent item

        Returns:
            List[Dict]: List of child items
        """
        try:
            client = self.get_client()

            logging.debug(f"Searching for items under parent {parent_id} using abstractitems with pagination")

            # Get all items in the project using pagination
            all_items = []
            start_at = 0
            max_results = 50  # Jama's maximum per page

            while True:
                logging.debug(f"Fetching items starting at {start_at} with max {max_results}")

                # Get items with pagination parameters
                items_page = client.get_abstract_items(
                    project=self.project_id,
                    start_at=start_at,
                    max_results=max_results
                )

                if not items_page:
                    logging.debug(f"No more items found at start_at={start_at}")
                    break

                all_items.extend(items_page)
                logging.debug(f"Retrieved {len(items_page)} items, total so far: {len(all_items)}")

                # If we got fewer items than max_results, we've reached the end
                if len(items_page) < max_results:
                    logging.debug(f"Reached end of items (got {len(items_page)} < {max_results})")
                    break

                start_at += max_results

            logging.debug(f"Total items in project: {len(all_items)}")

            # Filter for items that have this parent
            children = []
            for item in all_items:
                item_parent = item.get('location', {}).get('parent')
                if item_parent == parent_id:
                    children.append(item)

            logging.debug(f"Found {len(children)} items under parent {parent_id}")

            return children

        except Exception as e:
            logging.error(f"Error getting children for item {parent_id} via location search: {e}")
            logging.debug(f"Exception details: {e}")
            return []

    def find_or_create_module_folder(self, module_name: str, parent_item: Dict) -> Dict:
        """
        Find or create a module folder under the configured test set using location search.

        Args:
            module_name: Name of the module
            parent_item: Configured test set container item data

        Returns:
            Dict: Module folder item data
        """
        try:
            client = self.get_client()
            parent_id = parent_item['id']

            logging.debug(f"Using test set ID {parent_id} for module folder search")

            # Try both methods: children API and location search
            # Both methods now support pagination to handle folders with >20 items
            children = self.get_children_items(parent_id)

            if not children:
                logging.debug("Children API returned 0, trying location search...")
                children = self.get_children_items_by_location(parent_id)

            # Look for existing module folder in direct children
            for child in children:
                if (child.get('fields', {}).get('name') == module_name and
                    child.get('itemType') == ITEM_TYPES['FOLDER']):
                    logging.info(f"Found existing module folder: {module_name}")
                    return child

            # Create new module folder if not found
            logging.info(f"Creating new module folder: {module_name}")

            # The issue was here - let's try different approaches
            logging.debug(f"Creating folder with:")
            logging.debug(f"    project: {self.project_id}")
            logging.debug(f"    item_type_id: {ITEM_TYPES['FOLDER']} (FOLDER)")
            logging.debug(f"    child_item_type_id: {ITEM_TYPES['UNIT_TEST']} (UNIT_TEST - what should go inside)")
            logging.debug(f"    location: {parent_id} (test set)")

            result_id = client.post_item(
                project=self.project_id,
                item_type_id=ITEM_TYPES['FOLDER'],
                child_item_type_id=ITEM_TYPES['UNIT_TEST'],  # Changed: folder should contain unit tests, not folders
                location=parent_id,
                fields={
                    'name': module_name,
                    'description': f"Unit tests for {module_name} module"
                }
            )

            # Get the created item
            created_item = client.get_abstract_item(result_id)
            logging.info(f"Created module folder: {module_name} (ID: {result_id})")
            return created_item

        except APIException as e:
            logging.error(f"Error creating module folder '{module_name}': {e}")
            logging.debug(f"APIException details: {e}")
            raise JamaConnectionError(f"Failed to create module folder '{module_name}': {e}")

    def normalize_test_name(self, test_name: str) -> str:
        """
        Normalize test name for comparison by removing prefixes and suffixes.

        Args:
            test_name: Raw test name from parsing

        Returns:
            str: Normalized test name for comparison
        """
        # Remove "Test case: " prefix if present
        normalized = test_name
        if normalized.startswith("Test case: "):
            normalized = normalized[11:]  # Remove "Test case: "

        # Remove "Scenario: " prefix if present
        if normalized.startswith("Scenario: "):
            normalized = normalized[10:]  # Remove "Scenario: "

        # Remove status suffixes like " 🟢 PASS", " 🔴 FAIL", etc.
        # First remove emoji + status word combinations
        normalized = re.sub(r'\s+[🟢🔴⚪]\s+(PASS|FAIL|SKIP)\s*$', '', normalized)
        # Then remove lone emojis at the end
        normalized = re.sub(r'\s+[🟢🔴⚪]\s*$', '', normalized)

        # Apply general Unicode cleaning to ensure all emojis are removed
        normalized = clean_log_message(normalized)

        # Strip whitespace
        normalized = normalized.strip()

        return normalized

    def _create_test_description(self, test_content: Dict, covers_list: List[str] = None) -> str:
        """
        Create a detailed description for the unit test based on actual test content.

        Args:
            test_content: The parsed test content (scenario data)
            covers_list: List of requirement IDs that this test covers

        Returns:
            str: HTML-formatted description with actual test steps
        """
        # Pre-compile the regex for better performance (used in multiple places)
        status_re = re.compile(r'\s+[🟢🔴⚪]\s+(PASS|FAIL|SKIP)\s*$')
        description_parts = []

        # Handle structured test content (with Given-When-Then steps)
        if 'steps' in test_content:
            steps = test_content['steps']
            for step in steps:
                step_lines = []
                # Use a loop to avoid code duplication
                for key, label in [('given', 'Given'), ('when', 'When'), ('then', 'Then')]:
                    if key in step:
                        clean = status_re.sub('', step[key]).strip()
                        step_lines.append(f"<strong>{label}:</strong> {clean}")

                # Add this step group to description with HTML formatting
                if step_lines:
                    description_parts.extend(step_lines)
                    description_parts.append("")  # Add blank line between step groups

        # Handle unstructured content (raw lines)
        elif 'raw_lines' in test_content:
            for line in test_content['raw_lines']:
                clean_line = line.strip()
                # Skip covers lines and empty lines
                if clean_line and not clean_line.lower().startswith('covers:'):
                    # Remove status indicators using the same regex
                    clean_line = status_re.sub('', clean_line).strip()
                    if clean_line:
                        description_parts.append(clean_line)

        # Handle XML content
        elif 'xml_content' in test_content:
            description_parts.append("<strong>XML-based unit test</strong>")
            xml_data = test_content['xml_content']
            if isinstance(xml_data, dict):
                if 'name' in xml_data:
                    description_parts.append(f"<strong>Test Suite:</strong> {xml_data['name']}")
                if 'tests' in xml_data:
                    description_parts.append(f"<strong>Contains:</strong> {xml_data['tests']} test cases")

        # Join all parts with HTML line breaks and remove trailing empty lines
        if description_parts:
            # Remove empty trailing lines
            while description_parts and description_parts[-1] == "":
                description_parts.pop()

            # Convert to HTML with proper line breaks
            html_parts = []
            for part in description_parts:
                if part == "":
                    html_parts.append("<br><br>")  # Double line break for separation
                else:
                    html_parts.append(part)

            # Join with single line breaks
            description = "<br>".join(html_parts)
        else:
            description = "Automated unit test created from test report"

        return description

    def find_or_create_unit_test(self, test_name: str, module_folder: Dict, covers_list: List[str] = None, test_content: Dict = None, ut_id: str = None) -> Dict:
        """
        Find existing unit test or create new one. Updates existing test if description or name has changed.
        If a UT ID is declared but not found, raises JamaConnectionError and does not fallback to name-based search.

        Args:
            test_name: Name of the unit test
            module_folder: Module folder data from Jama
            covers_list: List of requirement document keys
            test_content: Test content for generating description
            ut_id: Explicit UT ID to use (if provided)

        Returns:
            Dict: Unit test item data
        Raises:
            JamaItemNotFoundError: If a UT ID is declared but not found in Jama
        """
        def _normalize_description(text):
            text = re.sub(r'<[^>]+>', '', text or '').strip()
            text = text.replace('\xa0', ' ')
            text = text.replace('\u00a0', ' ')
            text = text.replace('\r', '')
            text = text.replace('\t', ' ')
            text = text.replace('\n', ' ')
            text = re.sub(r'\s+', ' ', text)
            return text.lower().strip()
        try:
            covers_list = list(covers_list) if covers_list else []
            normalized_test_name = self.normalize_test_name(test_name)
            expected_description = self._create_test_description(test_content, covers_list)
            if ut_id is not None:
                ut_item = self.get_item_by_document_key(ut_id, item_type=ITEM_TYPES['UNIT_TEST'])
                if ut_item:
                    current_description = ut_item.get('fields', {}).get('description', '').strip()
                    current_name = ut_item.get('fields', {}).get('name', '').strip()
                    clean_current_desc = _normalize_description(current_description)
                    clean_expected_desc = _normalize_description(expected_description)
                    clean_current_name = self.normalize_test_name(current_name)
                    clean_expected_name = normalized_test_name
                    needs_update = False
                    update_fields = {}
                    if clean_current_desc != clean_expected_desc:
                        needs_update = True
                        update_fields['description'] = expected_description
                        logging.info(f"Description has changed")
                        logging.info(f"   '{clean_current_desc}'")
                        logging.info(f"   '{clean_expected_desc}'")

                    if clean_current_name != clean_expected_name:
                        needs_update = True
                        update_fields['name'] = normalized_test_name
                        logging.info(f"Name has changed")
                        logging.info(f"   '{clean_current_name}'")
                        logging.info(f"   '{clean_expected_name}'")

                    if needs_update:
                        logging.info(f"UT ID {ut_id}: Name or description differs - updating via workflow transitions")
                        self.update_test_with_workflow_transitions(ut_item['id'], new_description=update_fields.get('description'), new_name=update_fields.get('name'))
                        logging.info(f"UT ID {ut_id}: Name/Description updated")
                    else:
                        logging.info(f"UT ID {ut_id}: Name and description match - no update needed")
                    return ut_item
                else:
                    logging.error(f"UT ID {ut_id} declared but not found in Jama. Skipping name-based search and raising error.")
                    raise JamaItemNotFoundError(f"UT ID '{ut_id}' declared but not found in Jama.")
            # Fallback to name-based search/create only if no UT ID declared
            clean_test_name = clean_log_message(test_name)
            clean_normalized_name = clean_log_message(normalized_test_name)
            logging.info(f"Looking for existing UT: '{clean_log_message(clean_normalized_name)}' (normalized from: '{clean_log_message(clean_test_name)}')")
            existing_unit_test = None
            children = self.get_children_items(module_folder['id'])
            if children is None:
                logging.debug("Children API failed, trying location search...")
                children = self.get_children_items_by_location(module_folder['id'])
            elif len(children) == 0:
                logging.debug(f"Folder is empty (no existing unit tests)")
                children = []

            # Debug: Count unit tests in children
            unit_test_count = sum(1 for child in children if child.get('itemType') == ITEM_TYPES['UNIT_TEST'])
            logging.debug(f"Found {unit_test_count} unit tests in folder to compare against")

            for child in children:
                if child.get('itemType') == ITEM_TYPES['UNIT_TEST']:
                    existing_name = child.get('fields', {}).get('name', '').strip()
                    normalized_existing = self.normalize_test_name(existing_name)
                    logging.debug(f"Comparing: '{normalized_existing}' == '{normalized_test_name}'")
                    if normalized_existing == normalized_test_name:
                        existing_unit_test = child
                        logging.info(f"Found existing unit test: {clean_log_message(existing_name)}")
                        break
            if existing_unit_test:
                current_description = existing_unit_test.get('fields', {}).get('description', '').strip()
                clean_current = _normalize_description(current_description)
                clean_expected = _normalize_description(expected_description)
                if clean_current != clean_expected:
                    logging.info(f"Description differs - updating existing test")
                    diff = list(difflib.unified_diff(
                        clean_current.split(), clean_expected.split(),
                        fromfile='current', tofile='expected', lineterm=''))
                    if diff:
                        logging.info("   Diff:")
                        for line in diff:
                            logging.info(line)
                    self.update_test_with_workflow_transitions(existing_unit_test['id'], new_description=expected_description)
                    logging.info(f"Updated description for existing test: {existing_unit_test['id']}")
                    return existing_unit_test
                else:
                    logging.info(f"Description matches - no update needed")
                return existing_unit_test
            else:
                logging.info(f"Creating new unit test: {clean_log_message(normalized_test_name)}")
                client = self.get_client()
                result_id = client.post_item(
                    project=self.project_id,
                    item_type_id=ITEM_TYPES['UNIT_TEST'],
                    child_item_type_id=ITEM_TYPES['UNIT_TEST'],
                    location=module_folder['id'],
                    fields={
                        'name': normalized_test_name,
                        'description': expected_description
                    }
                )
                logging.info(f"Created unit test: {clean_log_message(normalized_test_name)} (ID: {result_id})")
                created_item = client.get_abstract_item(result_id)
                return created_item
        except Exception as e:
            logging.error(f"Error in find_or_create_unit_test: {e}")
            raise

    def get_existing_relationships_for_unit_test(self, unit_test_id: int) -> List[Dict]:
        """
        Get all existing relationships where the unit test is the 'to' item using upstream relationships.

        Args:
            unit_test_id: The ID of the unit test

        Returns:
            List[Dict]: List of relationship data with 'from_item' information

        Raises:
            JamaConnectionError: If unable to retrieve relationships
        """
        try:
            client = self.get_client()

            logging.debug(f"Getting upstream relationships for unit test {unit_test_id}")

            # Use the proper Jama client method for upstream relationships
            # This gets relationships where the unit test is the 'to' item (requirement -> UT)
            relationships = client.get_items_upstream_relationships(unit_test_id)

            if relationships:
                logging.debug(f"Found {len(relationships)} upstream relationships for unit test {unit_test_id}")
                return relationships
            else:
                logging.debug(f"No upstream relationships found for unit test {unit_test_id}")
                return []

        except Exception as e:
            logging.error(f"Error getting upstream relationships for unit test {unit_test_id}: {e}")
            raise JamaConnectionError(f"Failed to get upstream relationships for unit test {unit_test_id}: {e}")

    def create_verification_relationships(self, unit_test: Dict, covers_list: List[str]) -> Dict:
        """
        Create relationships between unit test and requirements, detecting orphaned relationships.
        Only creates missing relationships and warns about orphaned ones.

        Args:
            unit_test: Unit test item data
            covers_list: List of requirement document keys from covers field

        Returns:
            Dict: Detailed results with created, existing, orphaned, and failed relationships

        Raises:
            JamaConnectionError: If any errors occurred during relationship creation
        """
        if not covers_list:
            logging.info("No covers requirements to process")
            return {
                'success': True,
                'created_relationships': [],
                'existing_relationships': [],
                'orphaned_relationships': [],
                'failed_requirements': [],
                'error_message': None
            }

        # Use covers list as-is (search/replace functionality removed)
        processed_covers_list = covers_list

        # Filter out invalid requirement patterns
        valid_requirements = []
        invalid_requirements = []

        for req in processed_covers_list:
            if is_valid_requirement_pattern(req):
                valid_requirements.append(req)
            else:
                invalid_requirements.append(req)
                logging.warning(f"Ignoring invalid requirement pattern: {clean_log_message(req)} (does not match xxx-yyy-zzz format)")

        if invalid_requirements:
            logging.info(f"Filtered out {len(invalid_requirements)} invalid requirements: {clean_log_message(', '.join(invalid_requirements))}")

        if not valid_requirements:
            logging.info("No valid requirements to process after filtering")
            return {
                'success': True,
                'created_relationships': [],
                'existing_relationships': [],
                'orphaned_relationships': [],
                'failed_requirements': [],
                'error_message': None
            }

        try:
            client = self.get_client()
            unit_test_id = unit_test['id']
            unit_test_doc_key = unit_test.get('documentKey', 'Unknown')

            # Get existing relationships for this unit test
            existing_relationships = self.get_existing_relationships_for_unit_test(unit_test_id)

            # Extract document keys of related items from existing relationships
            existing_related_doc_keys = []
            for relationship in existing_relationships:
                # For upstream relationships, the 'from' item is the requirement
                # and the 'to' item is the unit test
                from_item_id = relationship.get('fromItem')
                if from_item_id:
                    # Get the related item to get its document key
                    try:
                        related_item = client.get_abstract_item(from_item_id)
                        related_doc_key = related_item.get('documentKey')
                        if related_doc_key:
                            existing_related_doc_keys.append(related_doc_key)
                    except Exception as e:
                        logging.warning(f"Could not get document key for related item {from_item_id}: {e}")

            # Find orphaned relationships (exist in Jama but not in covers list)
            orphaned_relationships = []
            for related_doc_key in existing_related_doc_keys:
                if related_doc_key not in valid_requirements:
                    orphaned_relationships.append({
                        'ut_doc_key': unit_test_doc_key,
                        'related_doc_key': related_doc_key
                    })
                    logging.warning(f"Unit test {unit_test_doc_key} has relationship to {related_doc_key} that is not in current cover list")

            # Find relationships that need to be created (in covers list but not in Jama)
            relationships_to_create = [req for req in valid_requirements if req not in existing_related_doc_keys]

            # Find relationships that already exist
            existing_relationships_in_covers = [req for req in valid_requirements if req in existing_related_doc_keys]

            created_relationships = []
            failed_requirements = []
            error_details = []

            if relationships_to_create:
                logging.info(f"Creating {len(relationships_to_create)} new relationships")
                logging.info(f"Relationships to create: {clean_log_message(', '.join(relationships_to_create))}")

                for i, requirement_doc_key in enumerate(relationships_to_create, 1):
                    logging.info(f"Processing requirement {i}/{len(relationships_to_create)}: {clean_log_message(requirement_doc_key)}")

                    try:
                        # Check if requirement exists using efficient search
                        req_item = self.get_item_by_document_key(requirement_doc_key)

                        if not req_item:
                            error_msg = f"Requirement not found: {clean_log_message(requirement_doc_key)}"
                            logging.error(f"{i}/{len(relationships_to_create)} {error_msg}")
                            failed_requirements.append(requirement_doc_key)
                            error_details.append(f"{requirement_doc_key}: not found in Jama")
                            continue

                        req_id = req_item['id']
                        req_item_type = req_item.get('itemType')
                        logging.info(f"{i}/{len(relationships_to_create)} Found requirement {clean_log_message(requirement_doc_key)} (ID: {req_id}, Type: {req_item_type})")

                        # Determine relationship type based on item type and relationship tables
                        relationship_type = determine_relationship_type_for_unit_test(req_item)

                        relationship_params = {
                            'from_item': req_id,              # FROM: Requirement
                            'to_item': unit_test_id           # TO: Unit Test
                        }

                        # Add relationship type if specified (None means use default)
                        if relationship_type is not None:
                            relationship_params['relationship_type'] = relationship_type
                            logging.info(f"{i}/{len(relationships_to_create)} Using relationship type: {relationship_type}")
                        else:
                            logging.info(f"{i}/{len(relationships_to_create)} Using default relationship type")

                        # Try to create verification relationship (will fail if it already exists)
                        try:
                            # Temporarily suppress ERROR logging for "already exists" cases
                            jama_logger = logging.getLogger('py_jama_rest_client')
                            original_level = jama_logger.level
                            jama_logger.setLevel(logging.CRITICAL)

                            try:
                                relationship_id = client.post_relationship(**relationship_params)
                                jama_logger.setLevel(original_level)  # Restore logging level
                                logging.info(f"{i}/{len(relationships_to_create)} Created relationship: {requirement_doc_key} -> UT (ID: {relationship_id})")
                                created_relationships.append(requirement_doc_key)

                            except APIException as api_e:
                                jama_logger.setLevel(original_level)  # Restore logging level

                                # Check if relationship already exists
                                if "already exists" in str(api_e).lower() or "duplicate" in str(api_e).lower():
                                    logging.info(f"{i}/{len(relationships_to_create)} Relationship already exists: {requirement_doc_key} -> UT")
                                    created_relationships.append(requirement_doc_key)
                                else:
                                    # Some other API error - this should be logged
                                    error_msg = f"Failed to create relationship to {requirement_doc_key}: {api_e}"
                                    logging.error(f"{i}/{len(relationships_to_create)} {error_msg}")
                                    failed_requirements.append(requirement_doc_key)
                                    error_details.append(f"{requirement_doc_key}: API error - {str(api_e)}")
                                    continue

                        except Exception as e:
                            # Restore logging level in case of unexpected exceptions
                            jama_logger.setLevel(original_level)
                            raise e

                    except JamaConnectionError as e:
                        error_msg = f"Failed to process requirement {requirement_doc_key}: {e}"
                        logging.error(f"{i}/{len(relationships_to_create)} {error_msg}")
                        failed_requirements.append(requirement_doc_key)
                        error_details.append(f"{requirement_doc_key}: connection error - {str(e)}")
                        continue
            else:
                logging.debug("No new relationships to create")

            # Summary
            total_requirements = len(valid_requirements)
            failed_count = len(failed_requirements)
            orphaned_count = len(orphaned_relationships)

            logging.debug(f"Relationship management summary:")
            logging.debug(f"   Total requirements: {total_requirements}")
            logging.debug(f"   Created relationships: {len(created_relationships)}")
            logging.debug(f"   Existing relationships: {len(existing_relationships_in_covers)}")
            logging.debug(f"   Orphaned relationships: {orphaned_count}")
            logging.debug(f"   Failed requirements: {failed_count}")

            if failed_count > 0:
                logging.error(f"   Failed requirement IDs: {', '.join(failed_requirements)}")

                # Create detailed error message
                error_summary = f"Failed to create relationships for {failed_count} out of {total_requirements} requirements:\n"
                for error in error_details:
                    error_summary += f"  - {error}\n"

                return {
                    'success': False,
                    'created_relationships': created_relationships,
                    'existing_relationships': existing_relationships_in_covers,
                    'orphaned_relationships': orphaned_relationships,
                    'failed_requirements': failed_requirements,
                    'error_message': error_summary.rstrip()
                }

            return {
                'success': True,
                'created_relationships': created_relationships,
                'existing_relationships': existing_relationships_in_covers,
                'orphaned_relationships': orphaned_relationships,
                'failed_requirements': failed_requirements,
                'error_message': None
            }

        except APIException as e:
            logging.error(f"Error creating verification relationships: {e}")
            return {
                'success': False,
                'created_relationships': [],
                'existing_relationships': [],
                'orphaned_relationships': [],
                'failed_requirements': [],
                'error_message': f"Failed to create verification relationships: {e}"
            }

    def get_available_workflow_transitions(self, item_id: int) -> List[Dict]:
        """
        Get all available workflow transitions for a Jama item.

        Args:
            item_id: The ID of the Jama item

        Returns:
            List[Dict]: List of available transitions

        Raises:
            JamaConnectionError: If unable to retrieve transitions
        """
        try:
            client = self.get_client()
            core = client._JamaClient__core

            logging.debug(f"Getting available workflow transitions for item {item_id}")
            transitions_url = f"items/{item_id}/workflowtransitionoptions"

            transitions_response = core.get(transitions_url)
            if transitions_response.status_code != 200:
                logging.error(f"Failed to get workflow transitions for item {item_id}: {transitions_response.status_code}")
                raise JamaConnectionError(f"Failed to get workflow transitions for item {item_id}: {transitions_response.status_code}")

            transitions_data = transitions_response.json()
            available_transitions = transitions_data.get('data', [])

            logging.debug(f"Found {len(available_transitions)} available transitions for item {item_id}")

            # Log available transitions for debugging
            for transition in available_transitions:
                transition_id = transition.get('id')
                action = transition.get('action')
                new_status = transition.get('newStatus')
                new_status_name = get_status_name_from_id(new_status)
                logging.debug(f"  Transition: {action} -> {new_status_name} (ID: {transition_id})")

            return available_transitions

        except Exception as e:
            logging.error(f"Error getting workflow transitions for item {item_id}: {e}")
            raise JamaConnectionError(f"Failed to get workflow transitions for item {item_id}: {e}")

    def change_item_status(self, item_id: int, target_status: str, comment: str = None) -> bool:
        """
        Change the workflow status of a Jama item to a target status using proper workflow transitions.

        This method uses the Jama REST API's workflow transition endpoints to properly
        respect workflow transition rules.

        Args:
            item_id: The ID of the Jama item to update
            target_status: The target status name (e.g., 'Accepted', 'Rework', 'Review', 'Draft')
            comment: Optional comment for the transition

        Returns:
            bool: True if status change was successful, False otherwise

        Raises:
            JamaConnectionError: If the status change fails
        """
        try:
            client = self.get_client()

            # First, get the current item to check its current status
            current_item = client.get_abstract_item(item_id)
            current_status_id = current_item.get('fields', {}).get(WORKFLOW_STATUS_FIELD, 'Unknown')

            current_status_name = get_status_name_from_id(current_status_id)
            logging.debug(f"Current workflow status for item {item_id}: '{current_status_name}' (ID: {current_status_id})")

            # Check if target status is valid
            if target_status not in WORKFLOW_STATUS_IDS:
                raise JamaConnectionError(f"Invalid target status: {target_status}. Valid statuses: {list(WORKFLOW_STATUS_IDS.keys())}")

            target_status_id = WORKFLOW_STATUS_IDS[target_status]

            # If already in target state, no change needed
            if current_status_id == target_status_id:
                logging.debug(f"Item {item_id} is already in '{target_status}' status - no change needed")
                return True

            # Get available workflow transitions
            available_transitions = self.get_available_workflow_transitions(item_id)

            # Execute transitions to reach target status
            return self._execute_transitions_to_status(item_id, target_status, available_transitions, comment)

        except APIException as e:
            logging.error(f"Failed to change workflow status for item {item_id}: {e}")
            raise JamaConnectionError(f"Failed to change workflow status for item {item_id}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error changing workflow status for item {item_id}: {e}")
            raise JamaConnectionError(f"Unexpected error changing workflow status for item {item_id}: {e}")

    def _execute_transitions_to_status(self, item_id: int, target_status: str, available_transitions: List[Dict], comment: str = None) -> bool:
        """
        Execute workflow transitions to reach a target status.

        Args:
            item_id: The ID of the Jama item
            target_status: The target status name
            available_transitions: List of available transitions from the API
            comment: Optional comment for transitions

        Returns:
            bool: True if transitions were successful

        Raises:
            JamaConnectionError: If no valid transition path is found or execution fails
        """
        # Create a map of transitions by action name for easy lookup
        transitions_by_action = {t.get('action'): t for t in available_transitions}

        # Define the transition path to reach target status
        # For Accepted: try direct transition first, then multi-step if needed
        transition_path = []

        if target_status == 'Accepted':
            # Check if we can go directly to Accepted
            if 'Accepted' in transitions_by_action:
                transition_path.append('Accepted')
            elif 'Review' in transitions_by_action:
                transition_path.append('Review')
                transition_path.append('Accepted')
        else:
            # For other statuses, try direct transition
            if target_status in transitions_by_action:
                transition_path.append(target_status)

        if not transition_path:
            logging.warning(f"No valid transition path found to reach {target_status} status for item {item_id}")
            logging.warning(f"Available transitions: {list(transitions_by_action.keys())}")
            raise JamaConnectionError(f"No valid transition path found to reach {target_status} status for item {item_id}")

        # Execute each transition in the path
        for i, action in enumerate(transition_path, 1):
            if action not in transitions_by_action:
                logging.error(f"Transition action '{action}' not available for item {item_id}")
                raise JamaConnectionError(f"Transition action '{action}' not available for item {item_id}")

            transition = transitions_by_action[action]
            transition_id = transition.get('id')

            logging.debug(f"Step {i}: Executing transition '{action}' (ID: {transition_id}) for item {item_id}")

            try:
                # Execute the transition using the correct API structure
                client = self.get_client()
                core = client._JamaClient__core

                execute_url = f"items/{item_id}/workflowtransitions"
                transition_comment = comment or f"Automated transition to {action} status"
                body = {
                    "transitionId": transition_id,
                    "comment": transition_comment
                }
                headers = {'content-type': 'application/json'}

                execute_response = core.post(execute_url, data=json.dumps(body), headers=headers)

                # Accept both 200 and 201 as successful responses
                if execute_response.status_code not in [200, 201]:
                    logging.error(f"Failed to execute transition '{action}' for item {item_id}: {execute_response.status_code}")
                    logging.error(f"Response: {execute_response.text}")
                    raise JamaConnectionError(f"Failed to execute transition '{action}' for item {item_id}: {execute_response.status_code}")

                logging.debug(f"Successfully executed transition '{action}' for item {item_id}")

                # If this wasn't the last transition, get updated transitions for the next step
                if i < len(transition_path):
                    logging.debug(f"Getting updated transitions for next step...")
                    transitions_response = core.get(f"items/{item_id}/workflowtransitionoptions")
                    if transitions_response.status_code == 200:
                        updated_transitions_data = transitions_response.json()
                        available_transitions = updated_transitions_data.get('data', [])
                        transitions_by_action = {t.get('action'): t for t in available_transitions}

                        logging.debug(f"Updated transitions available: {list(transitions_by_action.keys())}")

                        # Check if the next action in our path is still available
                        next_action = transition_path[i]
                        if next_action not in transitions_by_action:
                            logging.error(f"Next transition action '{next_action}' not available after executing '{action}'")
                            raise JamaConnectionError(f"Next transition action '{next_action}' not available after executing '{action}'")
                    else:
                        logging.warning(f"Failed to get updated transitions: {transitions_response.status_code}")
                        raise JamaConnectionError(f"Failed to get updated transitions: {transitions_response.status_code}")

            except JamaConnectionError:
                # Re-raise JamaConnectionError as-is
                raise
            except Exception as e:
                logging.error(f"Error executing transition '{action}' for item {item_id}: {e}")
                raise JamaConnectionError(f"Error executing transition '{action}' for item {item_id}: {e}")

        logging.debug(f"Successfully completed all transitions to reach {target_status} status for item {item_id}")
        return True

    def change_item_status_to_accepted(self, item_id: int) -> bool:
        """
        Change the workflow status of a Jama item to 'Accepted' using proper workflow transitions.

        Args:
            item_id: The ID of the Jama item to update

        Returns:
            bool: True if status change was successful, False otherwise

        Raises:
            JamaConnectionError: If the status change fails
        """
        return self.change_item_status(item_id, 'Accepted', "Automated transition to Accepted status")

    def change_item_status_to_rework(self, item_id: int) -> bool:
        """
        Change the workflow status of a Jama item to 'Rework' using proper workflow transitions.

        Args:
            item_id: The ID of the Jama item to update

        Returns:
            bool: True if status change was successful, False otherwise

        Raises:
            JamaConnectionError: If the status change fails
        """
        return self.change_item_status(item_id, 'Rework', "Automated transition to Rework status for content update")

    def update_test_with_workflow_transitions(self, item_id: int, new_description: str = None, new_name: str = None) -> bool:
        """
        Update a test item following the proper workflow: Accepted -> Rework -> Update -> Accepted.
        Can update description, name, or both.

        Args:
            item_id: The ID of the Jama item to update
            new_description: The new description content (optional)
            new_name: The new name content (optional)

        Returns:
            bool: True if the complete workflow was successful

        Raises:
            JamaConnectionError: If any step in the workflow fails
        """
        try:
            client = self.get_client()
            # Get current item status
            current_item = client.get_abstract_item(item_id)
            current_status_id = current_item.get('fields', {}).get(WORKFLOW_STATUS_FIELD, 'Unknown')
            current_status_name = get_status_name_from_id(current_status_id)
            logging.debug(f"Starting workflow update for item {item_id} (current status: {current_status_name})")
            # Step 1: If currently Accepted, transition to Rework
            if current_status_id == WORKFLOW_STATUS_IDS['Accepted']:
                logging.info(f"Item {item_id} is in Accepted status - transitioning to Rework")
                self.change_item_status_to_rework(item_id)
            elif current_status_id == WORKFLOW_STATUS_IDS['Rework']:
                logging.debug(f"Item {item_id} is already in Rework status - proceeding with update")
            else:
                logging.info(f"Item {item_id} is in {current_status_name} status - proceeding with update")
            # Step 2: Update the test description and/or name
            patch_data = []
            if new_description is not None:
                patch_data.append({
                    'op': 'replace',
                    'path': '/fields/description',
                    'value': new_description
                })
            if new_name is not None:
                patch_data.append({
                    'op': 'replace',
                    'path': '/fields/name',
                    'value': new_name
                })
            if patch_data:
                updated_item = client.patch_item(item_id, patch_data)
                logging.debug(f"Successfully updated item {item_id} fields: {', '.join([p['path'] for p in patch_data])}")
            # Step 3: Transition back to Accepted status
            logging.debug(f"Transitioning item {item_id} back to Accepted status")
            self.change_item_status_to_accepted(item_id)
            logging.debug(f"Successfully completed workflow update for item {item_id}")
            return True
        except Exception as e:
            logging.error(f"Error in update_test_with_workflow_transitions for item {item_id}: {e}")
            raise JamaConnectionError(f"Failed to update test with workflow transitions: {e}")

    def get_test_groups_rest_api(self, test_plan_id: int) -> List[Dict]:
        """
        Get test groups from a test plan using direct REST API call.

        Args:
            test_plan_id: Test plan ID

        Returns:
            List[Dict]: List of test groups
        """
        try:
            client = self.get_client()
            # Access the underlying HTTP client from py_jama_rest_client
            core = client._JamaClient__core
            response = core.get(f"testplans/{test_plan_id}/testgroups")

            if response.status_code == 200:
                test_groups_data = response.json()
                return test_groups_data.get('data', [])
            else:
                logging.error(f"Failed to get test groups: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            logging.error(f"Error getting test groups via REST API: {e}")
            return []

    def get_test_cases_in_group_rest_api(self, test_plan_id: int, group_id: int) -> List[Dict]:
        """
        Get test cases in a specific test group using direct REST API call with pagination support.
        Handles the default 20-item limit by making multiple requests if needed.

        Args:
            test_plan_id: Test plan ID
            group_id: Test group ID

        Returns:
            List[Dict]: List of test cases in the group
        """
        try:
            client = self.get_client()
            # Access the underlying HTTP client from py_jama_rest_client
            core = client._JamaClient__core

            all_test_cases = []
            start_at = 0
            max_results = 50  # Jama's maximum per page

            while True:
                # Build URL with pagination parameters
                url = f"testplans/{test_plan_id}/testgroups/{group_id}/testcases?startAt={start_at}&maxResults={max_results}"
                logging.debug(f"Fetching test cases for group {group_id} starting at {start_at} with max {max_results}")

                response = core.get(url)

                if response.status_code == 200:
                    test_cases_data = response.json()
                    test_cases_page = test_cases_data.get('data', [])

                    if not test_cases_page:
                        logging.debug(f"No more test cases found at start_at={start_at}")
                        break

                    all_test_cases.extend(test_cases_page)
                    logging.debug(f"Retrieved {len(test_cases_page)} test cases, total so far: {len(all_test_cases)}")

                    # If we got fewer items than max_results, we've reached the end
                    if len(test_cases_page) < max_results:
                        logging.debug(f"Reached end of test cases (got {len(test_cases_page)} < {max_results})")
                        break

                    start_at += max_results
                else:
                    logging.error(f"Failed to get test cases for group {group_id}: {response.status_code} - {response.text}")
                    break

            logging.info(f"Retrieved total of {len(all_test_cases)} test cases for group {group_id}")
            return all_test_cases

        except Exception as e:
            logging.error(f"Error getting test cases for group {group_id} via REST API: {e}")
            return []

    def find_test_group_containing_case(self, test_plan_id: int, target_document_key: str) -> Optional[Dict]:
        """
        Find which test group contains a specific test case by document key.

        Args:
            test_plan_id: Test plan ID
            target_document_key: Document key to search for (e.g., "SmlPrep-IT-311" or "SmlPrep-UT-1")

        Returns:
            Dict or None: Test group containing the target test case, or None if not found
        """
        try:
            # Get all test groups for the test plan
            test_groups = self.get_test_groups_rest_api(test_plan_id)

            if not test_groups:
                logging.warning(f"No test groups found for test plan {test_plan_id}")
                return None

            logging.info(f"Searching for '{target_document_key}' in {len(test_groups)} test groups")

            # Check each group for the target test case
            for group in test_groups:
                group_id = group['id']
                group_name = group['name']

                logging.debug(f"Checking group: {group_name} (ID: {group_id})")

                # Get test cases in this group
                test_cases = self.get_test_cases_in_group_rest_api(test_plan_id, group_id)

                # Look for the target document key
                for test_case in test_cases:
                    if test_case.get('documentKey') == target_document_key:
                        logging.info(f"Found '{target_document_key}' in group: {group_name} (ID: {group_id})")
                        return group

            logging.warning(f"Target test case '{target_document_key}' not found in any test group")
            return None

        except Exception as e:
            logging.error(f"Error finding test group containing '{target_document_key}': {e}")
            return None


def validate_environment() -> bool:
    """
    Validate that all required environment variables are set.

    Returns:
        bool: True if all variables are set, False otherwise
    """
    # Check if global configuration is initialized
    if not GlobalConfig.is_initialized():
        logging.error("Global configuration has not been initialized")
        return False

    config = GlobalConfig.get_config()
    required_vars = [config['jama_url'], config['jama_client_id'], config['jama_client_password'], config['project_id']]
    if not all(required_vars):
        logging.error("Jama environment variables are not properly set")
        missing_vars = []
        if not config['jama_url']:
            missing_vars.append("JAMA_URL")
        if not config['jama_client_id']:
            missing_vars.append("JAMA_CLIENT_ID")
        if not config['jama_client_password']:
            missing_vars.append("JAMA_CLIENT_PASSWORD")
        if not config['project_id']:
            missing_vars.append("JAMA_DEFAULT_PROJECT_ID")

        logging.error(f"Missing variables: {', '.join(missing_vars)}")
        return False

    return True


def setup_logging(console_level: int = logging.INFO, log_file: Optional[str] = None, file_level: int = logging.DEBUG) -> None:
    """
    Setup logging configuration for UT operations.

    Args:
        console_level: Logging level for console output (default: INFO)
        log_file: Optional path to log file. If None, logs only to stdout
        file_level: Logging level for file output (default: DEBUG)
    """
    # Clear any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Console handler with specified level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logging.root.addHandler(console_handler)

    # File handler with DEBUG level (if specified)
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(file_level)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logging.root.addHandler(file_handler)

    # Set root logger to DEBUG to capture all levels
    logging.root.setLevel(logging.DEBUG)


def draw_table(headers: List[str], data: List[List[str]], column_ratios: str,
               title: str = None, total_width: int = 140) -> str:
    """
    Draw a formatted table with proportional column widths.

    Args:
        headers: List of column headers
        data: List of rows, each row is a list of cell values
        column_ratios: String defining column ratios (e.g., "Column1,1;Column2,3;Column3,1")
        title: Optional title to display above the table
        total_width: Total width of the table in characters

    Returns:
        str: Formatted table string

    Example:
        draw_table(
            ["Name", "Status", "Error"],
            [["Test1", "PASS", ""], ["Test2", "FAIL", "Connection error"]],
            "Name,2;Status,1;Error,3",
            "Test Results"
        )
    """
    # Parse column ratios
    ratio_parts = column_ratios.split(';')
    if len(ratio_parts) != len(headers):
        raise ValueError(f"Number of ratios ({len(ratio_parts)}) must match number of headers ({len(headers)})")

    # Extract ratios and calculate widths
    ratios = []
    for part in ratio_parts:
        if ',' in part:
            name, ratio = part.split(',', 1)
            ratios.append(int(ratio))
        else:
            ratios.append(1)

    # Calculate column widths based on ratios
    total_ratio = sum(ratios)
    column_widths = []

    for ratio in ratios:
        # Calculate proportional width, minimum 3 characters
        width = max(3, int((ratio / total_ratio) * (total_width - len(headers) - 1)))
        column_widths.append(width)

    # Adjust total width to account for separators
    actual_width = sum(column_widths) + len(headers) + 1

    # Build table
    lines = []

    # Add title if provided
    if title:
        lines.append(title)
        lines.append("")

    # Header row
    header_line = "|"
    separator_line = "|"

    for i, header in enumerate(headers):
        width = column_widths[i]
        header_line += f" {header:<{width}} |"
        separator_line += f"{'-' * (width + 2)}|"

    lines.append(header_line)
    lines.append(separator_line)

    # Data rows
    for row in data:
        data_line = "|"
        for i, cell in enumerate(row):
            width = column_widths[i]
            # Truncate cell content if it's too long
            if len(cell) > width:
                cell = cell[:width-3] + "..."
            data_line += f" {cell:<{width}} |"
        lines.append(data_line)

    return "\n".join(lines)


def clean_log_message(message: str) -> str:
    """
    Remove Unicode characters (emojis and symbols) from log messages for CI/CD compatibility.

    Args:
        message: Original log message potentially containing Unicode characters

    Returns:
        str: Cleaned message with Unicode characters removed
    """
    # Remove common emoji and symbol Unicode ranges (more comprehensive)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs (includes 🟢🔴⚪)
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # miscellaneous symbols
        "\U000024C2-\U0001F251"  # enclosed characters
        "\U00002600-\U000026FF"  # miscellaneous symbols
        "\U00002700-\U000027BF"  # dingbats
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
        "]+",
        flags=re.UNICODE
    )

    # Remove emojis and extra whitespace
    cleaned = emoji_pattern.sub('', message).strip()

    # Remove specific status patterns that might remain
    cleaned = re.sub(r'\s+(PASS|FAIL|SKIP)\s*$', '', cleaned)

    # Remove any remaining non-ASCII characters that might cause issues
    cleaned = re.sub(r'[^\x00-\x7F]+', '', cleaned)

    # Clean up multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)

    return cleaned


def is_valid_requirement_pattern(candidate: str) -> bool:
    """
    Returns True if the string matches the pattern xxx-yyy-zzz where z is a decimal number.
    The number of letters in x, y, or z is not restricted, but each part must have at least 1 character.

    Args:
        candidate: The requirement ID to validate

    Returns:
        bool: True if the pattern is valid, False otherwise
    """
    if not candidate or not isinstance(candidate, str):
        return False

    # Pattern: xxx-yyy-zzz where each part has at least 1 character and z is decimal
    # First two parts can contain letters, numbers, and underscores (but not dashes to avoid confusion)
    # Third part must be numeric only
    # This ensures exactly 3 parts separated by exactly 2 dashes
    pattern = r'^[A-Za-z0-9_]+-[A-Za-z0-9_]+-\d+$'
    return bool(re.match(pattern, candidate.strip()))


def is_jama_ut_id(candidate: str) -> bool:
    """
    Returns True if the string matches the pattern <project>-UT-<ID> (e.g., SmlPrep-UT-213).
    """
    return bool(re.match(r"^[A-Za-z0-9_]+-UT-\d+$", candidate.strip()))



def find_test_plan_by_version_and_prefix(version: str, prefix: str = "Unit and Integration Test Plans") -> Optional[Dict]:
    """
    Find test plan by version and prefix using contains parameter.

    Args:
        version: Version string for test plan naming
        prefix: Prefix for test plan name (default: "Unit and Integration Test Plans")

    Returns:
        Optional[Dict]: Test plan if found, None otherwise
    """
    try:
        jama_manager = JamaUTManager.get_instance()
        client = jama_manager.get_client()

        target_test_plan_pattern = f"{prefix} - {version}"

        search_results = client.get_abstract_items(
            project=jama_manager.project_id,
            contains=[target_test_plan_pattern]
        )

        if not search_results:
            logging.error(f"No test plan found matching pattern: {target_test_plan_pattern}")
            return None

        # Filter results to only include test plans (itemType == 35)
        test_plans = [item for item in search_results if item.get('itemType') == ITEM_TYPES['TEST_PLAN']]

        if not test_plans:
            logging.error(f"No test plans found matching pattern: {target_test_plan_pattern}. Found {len(search_results)} items but none are test plans.")
            # Log what we found for debugging
            for item in search_results:
                item_type = item.get('itemType', 'Unknown')
                item_name = item.get('fields', {}).get('name', 'Unknown')
                logging.error(f"  Found item: {item_name} (Type: {item_type})")
            return None

        # Use the first test plan that matches the pattern
        test_plan = test_plans[0]

        test_plan_id = test_plan['id']
        test_plan_name = test_plan['fields']['name']
        logging.info(f"Found test plan: {test_plan_name} (ID: {test_plan_id})")

        return test_plan

    except Exception as e:
        logging.error(f"Error finding test plan: {e}")
        return None


def find_test_group_containing_case(test_plan_id: int, target_document_key: str) -> Optional[Dict]:
    """
    Find test group containing a specific test case by document key.

    Args:
        test_plan_id: ID of the test plan to search in
        target_document_key: Document key of the test case to find (e.g., "SmlPrep-IT-311" or "SmlPrep-UT-1")

    Returns:
        Optional[Dict]: Test group if found, None otherwise
    """
    try:
        jama_manager = JamaUTManager.get_instance()
        client = jama_manager.get_client()

        # Get all test groups in the test plan
        test_groups = jama_manager.get_test_groups_rest_api(test_plan_id)

        if not test_groups:
            logging.error(f"No test groups found in test plan {test_plan_id}")
            return None

        # Search through each group for the target test case
        for group in test_groups:
            logging.info(f"Checking if {target_document_key} is in group: {group['name']} (ID: {group['id']})")
            group_id = group['id']
            group_name = group['name']

            # Get test cases in this group
            test_cases = jama_manager.get_test_cases_in_group_rest_api(test_plan_id, group_id)

            if not test_cases:
                continue

            # Check if target test case exists in this group
            for test_case in test_cases:
                test_case_doc_key = test_case.get('documentKey', '')
                logging.debug(f"Test case document key: {test_case_doc_key}")
                if test_case_doc_key == target_document_key:
                    logging.info(f"Found target test case {target_document_key} in group: {group_name} (ID: {group_id})")
                    return group

        logging.error(f"Test case {target_document_key} not found in any group of test plan {test_plan_id}")
        return None

    except Exception as e:
        logging.error(f"Error finding test group containing case: {e}")
        return None


def create_filtered_test_cycle_with_group(test_plan_id: int, cycle_name: str,
                                        start_date: str, end_date: str, group_ids: List[int]) -> Optional[int]:
    """
    Create a filtered test cycle with specific test groups.

    Args:
        test_plan_id: ID of the test plan
        cycle_name: Name for the test cycle
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        group_ids: List of group IDs to include in the cycle

    Returns:
        Optional[int]: Test cycle ID if created successfully, None otherwise
    """
    try:
        jama_manager = JamaUTManager.get_instance()
        client = jama_manager.get_client()

        # Create test cycle with filtered groups using the correct API call
        test_cycle_id = client.post_testplans_testcycles(
            testplan_id=test_plan_id,
            testcycle_name=cycle_name,
            start_date=start_date,
            end_date=end_date,
            testgroups_to_include=group_ids
        )

        if test_cycle_id:
            logging.info(f"Created test cycle: {cycle_name} (ID: {test_cycle_id})")
            return test_cycle_id
        else:
            logging.error("Failed to create test cycle - no ID returned")
            return None

    except Exception as e:
        logging.error(f"Error creating filtered test cycle: {e}")
        return None


def update_test_run_status(test_run_id: int, status: str, description: str = "") -> bool:
    """
    Update test run status and description.

    Args:
        test_run_id: ID of the test run to update
        status: New status (PASSED/FAILED/BLOCKED)
        description: Description for the test run

    Returns:
        bool: True if update succeeded, False otherwise
    """
    try:
        jama_manager = JamaUTManager.get_instance()
        client = jama_manager.get_client()

        # Map status to Jama status values
        # First, clean the status by removing emojis and normalizing
        import re
        clean_status = re.sub(r'[🟢🔴⚪❌⏭️]\s*', '', status).strip().upper()

        status_mapping = {
            'PASS': 'PASSED',
            'FAIL': 'FAILED',
            'SKIP': 'BLOCKED',
            'SKIPPED': 'BLOCKED',  # Handle both SKIP and SKIPPED
            'passed': 'PASSED',
            'failed': 'FAILED',
            'skipped': 'BLOCKED'
        }

        jama_status = status_mapping.get(clean_status, clean_status)

        # Log the status transformation for debugging
        if status != clean_status or clean_status != jama_status:
            logging.debug(f"Status transformation: '{status}' -> '{clean_status}' -> '{jama_status}'")

        # Update both status and actual results with detailed description
        run_data = {
            'fields': {
                'testRunStatus': jama_status
            }
        }

        # Add the detailed description to actualResults field
        if description:
            # Limit description to prevent API issues (Jama typically supports large text fields)
            limited_description = description[:8000]  # Increased limit for detailed descriptions
            run_data['fields']['actualResults'] = limited_description
            logging.debug(f"Adding {len(limited_description)} characters to actualResults field")

        # JSON-serialize the data as expected by put_test_run
        import json
        result = client.put_test_run(test_run_id, data=json.dumps(run_data))

        if result:
            logging.info(f"Successfully updated test run {test_run_id} to status: {jama_status}")
            return True
        else:
            logging.error(f"Failed to update test run {test_run_id}")
            return False

    except Exception as e:
        logging.error(f"Error updating test run {test_run_id}: {e}")
        return False


def get_test_runs_from_cycle(test_cycle_id: int) -> List[Dict]:
    """
    Get all test runs from a test cycle.

    Args:
        test_cycle_id: ID of the test cycle

    Returns:
        List[Dict]: List of test runs in the cycle
    """
    try:
        jama_manager = JamaUTManager.get_instance()
        client = jama_manager.get_client()

        test_runs = client.get_testruns(test_cycle_id)

        if test_runs:
            logging.info(f"Found {len(test_runs)} test runs in cycle {test_cycle_id}")
            return test_runs
        else:
            logging.warning(f"No test runs found in cycle {test_cycle_id}")
            return []

    except Exception as e:
        logging.error(f"Error getting test runs from cycle {test_cycle_id}: {e}")
        return []