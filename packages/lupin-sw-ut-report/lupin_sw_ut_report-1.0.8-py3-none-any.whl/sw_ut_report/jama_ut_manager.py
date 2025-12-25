"""
Jama Unit Test Manager - Orchestrates UT creation workflow.

This module handles the complete workflow for creating unit tests in Jama:
1. Validate SmlPrep-UT-1 exists
2. Find/create module folder
3. Find/create unit tests
4. Create verification relationships
"""

import logging
import re
from typing import Dict, List, Optional

from sw_ut_report.jama_common import (
    JamaUTManager, JamaConnectionError, JamaValidationError,
    JamaItemNotFoundError, JamaRequiredItemNotFoundError,
    validate_environment, clean_log_message, draw_table,
    is_jama_ut_id, ITEM_TYPES, is_valid_requirement_pattern
)


def _should_skip_test_scenario(scenario, filename: str) -> bool:
    """
    Check if a test scenario should be skipped based on the status in the test case name.

    Args:
        scenario: The test scenario (UnitTestCaseData object or dictionary)
        filename: The source filename for logging

    Returns:
        bool: True if the scenario should be skipped (FAIL/SKIP status), False if it should be processed (PASS status)
    """
    test_name = ""

    # Extract test name based on scenario type
    if hasattr(scenario, 'get_test_case_name'):
        # UnitTestCaseData object
        test_name = scenario.get_test_case_name()
    elif isinstance(scenario, dict):
        # Dictionary format
        if 'test_case' in scenario:
            # Structured scenario
            test_name = scenario['test_case']
        elif 'raw_lines' in scenario:
            # Unstructured scenario - get the first meaningful line
            for line in scenario['raw_lines']:
                clean_line = line.strip()
                if clean_line and not clean_line.lower().startswith('covers:'):
                    test_name = clean_line
                    break
        else:
            # Unknown format, skip to be safe
            logging.warning(f"Skipping scenario with unknown format in {filename}")
            return True
    else:
        # Unknown format, skip to be safe
        logging.warning(f"Skipping scenario with unknown format in {filename}")
        return True

    # Check for status indicators in the test name
    if '🔴 FAIL' in test_name or '⚪ SKIP' in test_name:
        logging.warning(f"Skipping failed/skipped test in {filename}: {clean_log_message(test_name)}")
        return True
    elif '🟢 PASS' in test_name:
        return False
    else:
        # No status indicator found, skip to be safe
        logging.warning(f"Skipping test with no status indicator in {filename}: {clean_log_message(test_name)}")
        return True


def dry_run_unit_tests_creation(module_name: str, test_results: List[Dict], project_id: Optional[str] = None, test_set_id: Optional[str] = None, ut_test_case_id: Optional[str] = None) -> int:
    """
    Dry-run function to analyze what would be done without making changes to Jama.
    Logs errors and continues processing. Returns appropriate exit code.

    Args:
        module_name: Name of the module (for folder creation)
        test_results: List of parsed test results from TXT/XML files

    Returns:
        int: 0 for success, 1 for errors, 2 for warnings only
    """
    logging.info(f"=== DRY-RUN: Analyzing Jama UT Creation for Module: {module_name} ===")

    # Validate environment first
    if not validate_environment():
        print("ISSUE: Jama environment not properly configured")
        return 1  # Error

    try:
        # Initialize Jama manager
        jama_manager = JamaUTManager.get_instance()
        print("Jama connection: OK")

        # Step 1: Check configured test set exists
        print(f"\n=== STEP 1: Checking {jama_manager.test_set_id} ===")
        try:
            test_set = jama_manager.validate_test_set_exists()
            print(f"FOUND: {jama_manager.test_set_id} exists - {test_set['fields']['name']}")
            print(f"   ID: {test_set['id']}")
        except (JamaConnectionError, JamaRequiredItemNotFoundError) as e:
            print(f"ISSUE: {e}")
            return 1  # Error

        # Step 2: Check module folder status
        print(f"\n=== STEP 2: Checking Module Folder: {module_name} ===")
        module_folder = _dry_run_check_module_folder(jama_manager, module_name, test_set)

        # Rest of the analysis remains the same...
        print(f"\n=== STEP 3: Analyzing Test Cases ===")
        planned_actions = []
        total_scenarios = 0
        skipped_tests = []  # Track names of skipped tests for dry-run

        for test_result in test_results:
            if test_result.get('type') == 'txt':
                scenarios = test_result.get('test_cases', [])

                for scenario in scenarios:
                    total_scenarios += 1

                    # Check if the scenario should be skipped due to status
                    if _should_skip_test_scenario(scenario, test_result.get('filename', 'Unknown')):
                        print(f"DRY-RUN: Would skip scenario due to status")
                        test_name = extract_test_name_from_scenario(scenario, test_result.get('filename', 'Unknown'))
                        skipped_tests.append(test_name)
                        continue

                    # Extract test name and covers using unified method
                    test_name = extract_test_name_from_scenario(scenario, test_result.get('filename', 'Unknown'))

                    # Extract covers list based on scenario type
                    if scenario.has_test_case():
                        covers_list = scenario.get_covers_list()
                        source_info = f"Structured TXT: {test_result.get('filename', 'Unknown')}"
                    elif scenario.has_raw_lines():
                        covers_list = scenario.get_covers_list()
                        source_info = f"Unstructured TXT: {test_result.get('filename', 'Unknown')}"
                    else:
                        print(f"SKIP: Unknown scenario format in {test_result.get('filename')}")
                        continue


                    # --- NEW LOGIC: Scan covers_list for UT IDs ---
                    ut_ids = [c for c in covers_list if is_jama_ut_id(c)]
                    covers_list_no_ut = [c for c in covers_list if not is_jama_ut_id(c)]
                    if len(ut_ids) > 1:
                        # Multiple UT IDs: skip and warn
                        print(f"ERROR: Multiple UT IDs found in covers for test '{test_name}': {ut_ids}. Only one is allowed.")
                        continue
                    elif len(ut_ids) == 1:
                        ut_id = ut_ids[0]
                        covers_list = covers_list_no_ut
                    else:
                        ut_id = None
                        covers_list = covers_list_no_ut
                    # --- END NEW LOGIC ---

                    # Analyze this test case
                    action = _dry_run_analyze_test_case(jama_manager, test_name, covers_list, source_info, module_folder, ut_id=ut_id)
                    planned_actions.append(action)

            elif test_result.get('type') == 'xml':
                total_scenarios += 1
                content = test_result.get('content', {})
                filename = test_result.get('filename', 'Unknown')
                test_name = content.get('name', filename.replace('.xml', '') if filename.endswith('.xml') else filename)
                covers_list = []
                source_info = f"XML: {filename}"

                # Analyze XML test case
                action = _dry_run_analyze_test_case(jama_manager, test_name, covers_list, source_info, module_folder)
                planned_actions.append(action)

        # Step 4: Summary Report
        print(f"\n=== DRY-RUN SUMMARY ===")
        print(f"  Module: {module_name}")
        print(f"  Total scenarios analyzed: {total_scenarios}")
        print(f"  Would skip due to status (FAIL/SKIP): {len(skipped_tests)}")

        # Display skipped tests as a table
        if skipped_tests:
            skipped_data = [[clean_log_message(test_name)] for test_name in skipped_tests]
            skipped_table = draw_table(
                headers=["Skipped Test Name"],
                data=skipped_data,
                column_ratios="Skipped Test Name,1",
                title="Skipped Tests (FAIL/SKIP status)"
            )
            print(f"\n{skipped_table}")

        # Count actions
        new_tests = sum(1 for a in planned_actions if a['action'] == 'CREATE_TEST')
        existing_tests = sum(1 for a in planned_actions if a['action'] == 'EXISTS_TEST')
        new_relationships = sum(len(a['new_relationships']) for a in planned_actions)
        existing_relationships = sum(len(a['existing_relationships']) for a in planned_actions)

        print(f"  Unit tests to CREATE: {new_tests}")
        print(f"  Unit tests that EXIST: {existing_tests}")
        print(f"  Relationships to CREATE: {new_relationships}")
        print(f"  Relationships that EXIST: {existing_relationships}")
        print(f"  Status changes to 'Accepted': {total_scenarios}")  # All tests will have status changed

        # Detailed action report
        print(f"\n=== DETAILED ACTIONS ===")
        for i, action in enumerate(planned_actions, 1):
            print(f"\n{i}. {action['test_name']}")
            if action.get('original_test_name') != action['test_name']:
                print(f"   Original: {action['original_test_name']}")
            print(f"   Source: {action['source_info']}")

            if action['action'] == 'CREATE_TEST':
                print(f"   ACTION: Create new unit test")
            else:
                print(f"   EXISTS: Unit test already exists (ID: {action.get('existing_id', 'Unknown')})")

            if action['covers_list']:
                print(f"   Covers: {', '.join(action['covers_list'])}")

                if action['new_relationships']:
                    print(f"   Will create {len(action['new_relationships'])} new relationships:")
                    for rel in action['new_relationships']:
                        print(f"      -> {rel}")

                if action['existing_relationships']:
                    print(f"   {len(action['existing_relationships'])} relationships already exist:")
                    for rel in action['existing_relationships']:
                        print(f"      -> {rel}")

                if action['invalid_requirements']:
                    print(f"   {len(action['invalid_requirements'])} invalid requirements:")
                    for req in action['invalid_requirements']:
                        print(f"      -> {req} (NOT FOUND IN JAMA)")
            else:
                print(f"   No covers requirements")

            # Status change information
            print(f"   STATUS: Will change workflow status to 'Accepted'")

        # Check for issues (removed unused variable)

        # Determine return code based on errors and warnings
        has_errors = any(a['invalid_requirements'] for a in planned_actions)
        has_warnings = len(skipped_tests) > 0

        if has_errors:
            print(f"\nISSUES DETECTED:")
            print(f"   Some requirement IDs in 'covers' fields don't exist in Jama")
            print(f"   These will cause errors during execution")

            # Collect all invalid requirements for error reporting
            all_invalid_reqs = []
            for action in planned_actions:
                all_invalid_reqs.extend(action['invalid_requirements'])

            error_msg = f"Invalid requirements found during dry-run: {', '.join(set(all_invalid_reqs))}"
            logging.error(error_msg)
            return 1  # Error
        elif has_warnings:
            print(f"\nWARNINGS DETECTED:")
            print(f"   Some tests would be skipped due to status")
            return 2  # Warning
        else:
            print(f"\nNO ISSUES DETECTED")
            print(f"   All requirements exist and operations look good!")
            return 0  # Success

    except (JamaConnectionError, JamaValidationError) as e:
        print(f"Jama operation failed: {e}")
        return 1  # Error
    except Exception as e:
        print(f"Unexpected error in dry-run analysis: {e}")
        return 1  # Error


def _dry_run_check_module_folder(jama_manager: JamaUTManager, module_name: str, parent_item: Dict) -> Optional[Dict]:
    """Check if module folder exists without creating it under the configured test set."""
    try:
        parent_id = parent_item['id']

        logging.debug(f"Using test set ID {parent_id} for module folder search")

        # Try both methods: children API and location search
        children = jama_manager.get_children_items(parent_id)

        if not children:
            logging.debug("Children API returned 0, trying location search...")
            children = jama_manager.get_children_items_by_location(parent_id)

        logging.debug(f"Found {len(children)} children under test set (ID: {parent_id})")

        # Debug: Show all children
        for i, child in enumerate(children):
            child_name = child.get('fields', {}).get('name', 'NO_NAME')
            child_type = child.get('itemType', 'NO_TYPE')
            child_id = child.get('id', 'NO_ID')
            logging.debug(f"   {i+1}. {child_name} (Type: {child_type}, ID: {child_id})")

        # Look for existing module folder in direct children
        for child in children:
            child_name = child.get('fields', {}).get('name')
            child_type = child.get('itemType')

            logging.debug(f"Comparing: '{child_name}' == '{module_name}' AND {child_type} == 32")

            if (child_name == module_name and child_type == 32):  # FOLDER type
                logging.debug(f"FOUND: Module folder '{module_name}' already exists")
                logging.debug(f"   ID: {child['id']}")
                return child

        logging.debug(f"WILL CREATE: Module folder '{module_name}' under test set")
        return {'id': 'NEW_FOLDER', 'fields': {'name': module_name}}  # Mock for analysis

    except Exception as e:
        logging.error(f"Error checking module folder: {e}")
        import traceback
        logging.debug(f"Full traceback: {traceback.format_exc()}")
        return None


def _dry_run_analyze_test_case(jama_manager: JamaUTManager, test_name: str, covers_list: List[str],
                              source_info: str, module_folder: Optional[Dict], ut_id: str = None) -> Dict:
    """Analyze a single test case for dry-run without making changes. Accepts explicit ut_id if found."""
    covers_list = list(covers_list) if covers_list else []


    normalized_test_name = jama_manager.normalize_test_name(test_name)
    action = {
        'test_name': normalized_test_name,
        'original_test_name': test_name,
        'source_info': source_info,
        'covers_list': covers_list,
        'action': 'CREATE_TEST',
        'existing_id': None,
        'new_relationships': [],
        'existing_relationships': [],
        'invalid_requirements': []
    }
    if ut_id and hasattr(jama_manager, 'get_item_by_document_key'):
        ut_item = jama_manager.get_item_by_document_key(ut_id, item_type=ITEM_TYPES['UNIT_TEST'])
        if ut_item:
            action['action'] = 'EXISTS_TEST'
            action['existing_id'] = ut_item['id']
        # else fallback to name-based search
    if not action['existing_id'] and module_folder and module_folder.get('id') != 'NEW_FOLDER':
        try:
            module_folder_id = module_folder['id']
            children = jama_manager.get_children_items(module_folder_id)
            if not children:
                children = jama_manager.get_children_items_by_location(module_folder_id)
            for child in children:
                if child.get('itemType') == 167:
                    existing_name = child.get('fields', {}).get('name', '').strip()
                    normalized_existing = jama_manager.normalize_test_name(existing_name)
                    logging.debug(f"DRY-RUN: Comparing '{normalized_existing}' == '{normalized_test_name}'")
                    if normalized_existing == normalized_test_name:
                        action['action'] = 'EXISTS_TEST'
                        action['existing_id'] = child['id']
                        logging.debug(f"DRY-RUN: Found existing test '{existing_name}' (ID: {child['id']})")
                        break
        except Exception as e:
            logging.error(f"Error checking existing tests: {e}")
    if covers_list:
        # Filter out invalid requirement patterns first
        valid_requirements = []
        invalid_patterns = []

        for req in covers_list:
            if is_valid_requirement_pattern(req):
                valid_requirements.append(req)
            else:
                invalid_patterns.append(req)
                logging.debug(f"DRY-RUN: Ignoring invalid requirement pattern: {req} (does not match xxx-yyy-zzz format)")

        if invalid_patterns:
            logging.debug(f"DRY-RUN: Filtered out {len(invalid_patterns)} invalid patterns: {', '.join(invalid_patterns)}")

        # Now check valid requirements against Jama
        for requirement_id in valid_requirements:
            try:
                req_item = jama_manager.get_item_by_document_key(requirement_id)
                if req_item:
                    action['new_relationships'].append(requirement_id)
                else:
                    action['invalid_requirements'].append(requirement_id)
            except (JamaConnectionError, JamaItemNotFoundError):
                action['invalid_requirements'].append(requirement_id)
    return action


def create_unit_tests_in_jama(module_name: str, test_results: List[Dict], project_id: Optional[str] = None, test_set_id: Optional[str] = None, ut_test_case_id: Optional[str] = None) -> int:
    """
    Create unit tests in Jama for the given module and test results.

    Args:
        module_name: Name of the module
        test_results: List of test results from parsing

    Returns:
        int: Exit code (0 for success, 1 for errors, 2 for warnings)
    """
    from .jama_common import JamaUTManager, JamaConnectionError, JamaItemNotFoundError, clean_log_message

    # Initialize Jama manager
    try:
        jama_manager = JamaUTManager.get_instance()
    except Exception as e:
        logging.error(f"Failed to initialize Jama manager: {e}")
        return 1

    # Validate that the configured test set exists
    try:
        parent_item = jama_manager.validate_test_set_exists()
        logging.info(f"Using test set: {parent_item['fields']['name']} (ID: {parent_item['id']})")
    except JamaConnectionError as e:
        logging.error(f"Failed to validate test set: {e}")
        return 1

    # Find or create module folder
    try:
        module_folder = jama_manager.find_or_create_module_folder(module_name, parent_item)
        logging.info(f"Using module folder: {module_folder['fields']['name']} (ID: {module_folder['id']})")
    except JamaConnectionError as e:
        logging.error(f"Failed to create/find module folder: {e}")
        return 1

    # Process test results
    total_scenarios = 0
    processed_count = 0
    skipped_count = 0
    skipped_tests = []
    name_based_ut_warnings = []
    ut_id_not_found_errors = []
    relationship_errors = []
    orphaned_relationship_warnings = []
    status_change_errors = []

    for test_result in test_results:
        if test_result.get('type') == 'txt':
            scenarios = test_result.get('test_cases', [])
            filename = test_result.get('filename', 'Unknown')

            for scenario in scenarios:
                total_scenarios += 1

                # Skip scenarios with FAIL or SKIP status
                if _should_skip_test_scenario(scenario, filename):
                    skipped_count += 1
                    test_name = extract_test_name_from_scenario(scenario, filename)
                    skipped_tests.append(test_name)
                    continue

                # Extract test name and covers using unified method
                test_name = extract_test_name_from_scenario(scenario, filename)

                # Extract covers list based on scenario type
                if scenario.has_test_case():
                    covers_list = scenario.get_covers_list()
                    ut_id = None  # Will be extracted from covers_list if present
                elif scenario.has_raw_lines():
                    covers_list = scenario.get_covers_list()
                    ut_id = None  # Will be extracted from covers_list if present
                else:
                    logging.warning(f"Unknown scenario format in {filename}")
                    continue
                # --- Scan covers_list for UT IDs ---
                ut_ids = [c for c in covers_list if is_jama_ut_id(c)]
                covers_list_no_ut = [c for c in covers_list if not is_jama_ut_id(c)]
                if len(ut_ids) > 1:
                    # Multiple UT IDs: skip and warn
                    name_based_ut_warnings.append({
                        'document_key': 'Multiple UT IDs',
                        'name': clean_log_message(test_name),
                        'error': f'Multiple UT IDs found in covers: {ut_ids}. Only one is allowed.'
                    })
                    logging.error(f"Multiple UT IDs found in covers for test '{test_name}' in file '{filename}': {ut_ids}")
                    continue
                elif len(ut_ids) == 1:
                    ut_id = ut_ids[0]
                    covers_list_for_relationships = covers_list_no_ut
                else:
                    ut_id = None
                    covers_list_for_relationships = covers_list_no_ut
                # --- END NEW LOGIC ---

                try:
                    # Convert UnitTestCaseData to dictionary format expected by find_or_create_unit_test
                    test_content_dict = {
                        'steps': scenario.get_steps() if hasattr(scenario, 'get_steps') else [],
                        'raw_lines': []  # UnitTestCaseData doesn't have raw lines
                    }

                    # Find or create unit test
                    unit_test = jama_manager.find_or_create_unit_test(
                        test_name=test_name,
                        module_folder=module_folder,
                        covers_list=covers_list_for_relationships,
                        test_content=test_content_dict,
                        ut_id=ut_id
                    )

                    # Track name-based UT warnings
                    if not ut_id:
                        name_based_ut_warnings.append({
                            'document_key': unit_test.get('documentKey', 'Unknown'),
                            'name': clean_log_message(test_name),
                            'error': 'Created/updated based on name search (no UT ID in covers)'
                        })

                    # Create relationships
                    if covers_list_for_relationships:
                        logging.debug(f"Creating relationships for {len(covers_list_for_relationships)} requirements")
                        try:
                            relationship_result = jama_manager.create_verification_relationships(unit_test, covers_list_for_relationships)

                            if relationship_result['success']:
                                logging.debug(f"Successfully processed relationships for {clean_log_message(test_name)}")

                                # Add orphaned relationship warnings to the list
                                if relationship_result['orphaned_relationships']:
                                    for orphaned in relationship_result['orphaned_relationships']:
                                        orphaned_relationship_warnings.append({
                                            'ut_doc_key': orphaned['ut_doc_key'],
                                            'related_doc_key': orphaned['related_doc_key'],
                                            'test_name': clean_log_message(test_name),
                                            'file_name': filename
                                        })

                                # Log relationship statistics
                                created_count = len(relationship_result['created_relationships'])
                                existing_count = len(relationship_result['existing_relationships'])
                                orphaned_count = len(relationship_result['orphaned_relationships'])

                                logging.debug(f"Relationships for {clean_log_message(test_name)}: {created_count} created, {existing_count} existing, {orphaned_count} orphaned")

                            else:
                                logging.error(f"Failed to create relationships for {clean_log_message(test_name)}: {relationship_result['error_message']}")
                                relationship_errors.append({
                                    'test_name': clean_log_message(test_name),
                                    'covers_list': covers_list_for_relationships,
                                    'error': relationship_result['error_message']
                                })

                        except JamaConnectionError as e:
                            logging.error(f"Failed to create relationships for {clean_log_message(test_name)}: {e}")
                            relationship_errors.append({
                                'test_name': clean_log_message(test_name),
                                'covers_list': covers_list_for_relationships,
                                'error': str(e)
                            })
                    else:
                        logging.info("No covers requirements found - no relationships to create")

                    try:
                        logging.debug(f"Changing workflow status to 'Accepted' for {clean_log_message(test_name)}")
                        jama_manager.change_item_status_to_accepted(unit_test['id'])
                        logging.debug(f"Successfully changed workflow status to 'Accepted' for {clean_log_message(test_name)}")
                    except JamaConnectionError as e:
                        logging.error(f"Failed to change workflow status for {clean_log_message(test_name)}: {e}")
                        status_change_errors.append({
                            'test_name': clean_log_message(test_name),
                            'test_id': unit_test['id'],
                            'error': str(e)
                        })

                    processed_count += 1

                except JamaItemNotFoundError as e:
                    logging.error(f"UT ID not found: {e}")
                    ut_id_not_found_errors.append({
                        'ut_id': ut_id or 'Unknown',
                        'test_name': clean_log_message(test_name),
                        'file_name': filename,
                        'error': str(e)
                    })
                    continue

                except JamaConnectionError as e:
                    logging.error(f"Failed to process test {clean_log_message(test_name)}: {e}")
                    relationship_errors.append({
                        'test_name': clean_log_message(test_name),
                        'covers_list': covers_list_for_relationships,
                        'error': str(e)
                    })
                    continue

            # Silently skip XML files
            # elif test_result.get('type') == 'xml':
            #     pass

            else:
                logging.warning(f"Skipping unknown test result type: {test_result.get('type')}")

    # Report final summary
    logging.info("=== UT Creation Summary ===")
    logging.info(f"Module: {module_name}")
    logging.info(f"Total scenarios processed: {total_scenarios}")
    logging.info(f"Skipped due to status (FAIL/SKIP): {skipped_count}")
    logging.info(f"Successfully created/updated: {processed_count}")

    # Display skipped tests as a table
    if skipped_tests:
        skipped_data = [[clean_log_message(test_name)] for test_name in skipped_tests]
        skipped_table = draw_table(
            headers=["Skipped Test Name"],
            data=skipped_data,
            column_ratios="Skipped Test Name,1",
            title="ERROR: Skipped Tests (FAIL/SKIP status)"
        )
        print(f"\n{skipped_table}")

    # Report name-based UT warnings
    if name_based_ut_warnings:
        warning_data = []
        for ut in name_based_ut_warnings:
            warning_data.append([
                ut['document_key'],
                ut['name'],
                ut['error']
            ])

        warning_table = draw_table(
            headers=["Document Key", "Test Name", "Error"],
            data=warning_data,
            column_ratios="Document Key,2;Test Name,4;Error,4",
            title="WARNING: UTs created/updated based on NAME search (not by UT ID)"
        )
        print(f"\n{warning_table}")

    # Report UT ID not found errors
    if ut_id_not_found_errors:
        error_data = []
        for ut in ut_id_not_found_errors:
            error_data.append([
                ut['ut_id'],
                ut['test_name'],
                ut['error']
            ])

        error_table = draw_table(
            headers=["UT ID", "Test Name", "Error"],
            data=error_data,
            column_ratios="UT ID,2;Test Name,4;Error,4",
            title="ERROR: UT IDs declared in covers but not found in Jama"
        )
        print(f"\n{error_table}")

    # Report orphaned relationship warnings
    if orphaned_relationship_warnings:
        orphaned_data = []
        for orphaned in orphaned_relationship_warnings:
            orphaned_data.append([
                orphaned['ut_doc_key'],
                orphaned['related_doc_key']
            ])

        orphaned_table = draw_table(
            headers=["UT Document Key", "Related Document Key"],
            data=orphaned_data,
            column_ratios="UT Document Key,2;Related Document Key,2",
            title="WARNING: Relationships exist in Jama but not in current cover list"
        )
        print(f"\n{orphaned_table}")

    # Report relationship creation errors as a table
    if relationship_errors:
        rel_error_data = []
        for error_info in relationship_errors:
            test_name = error_info['test_name']
            covers_count = len(error_info['covers_list'])
            error_msg = error_info['error']
            rel_error_data.append([
                test_name,
                str(covers_count),
                error_msg
            ])

        rel_error_table = draw_table(
            headers=["Test Name", "Failed Relationships", "Error"],
            data=rel_error_data,
            column_ratios="Test Name,3;Failed Relationships,1;Error,4",
            title="ERROR: Relationship Creation Failures"
        )
        print(f"\n{rel_error_table}")
    else:
        logging.info("All relationship operations completed successfully")

    # Report status change errors
    if status_change_errors:
        status_error_data = []
        for error_info in status_change_errors:
            test_name = error_info['test_name']
            test_id = error_info['test_id']
            error_msg = error_info['error']
            status_error_data.append([
                test_name,
                str(test_id),
                error_msg
            ])

        status_error_table = draw_table(
            headers=["Test Name", "Test ID", "Error"],
            data=status_error_data,
            column_ratios="Test Name,3;Test ID,1;Error,4",
            title="Workflow Status Change Failures"
        )
        print(f"\n{status_error_table}")
    else:
        logging.info("All workflow status changes completed successfully")

    # Handle case where no tests were processed
    if processed_count == 0:
        logging.warning("No unit tests were processed")
        return 1  # Error - no tests processed

    # Determine exit code based on warnings and errors
    has_warnings = bool(name_based_ut_warnings or orphaned_relationship_warnings)
    has_errors = bool(ut_id_not_found_errors or relationship_errors or status_change_errors)

    if has_errors:
        return 1  # Error exit code
    elif has_warnings:
        return 2  # Warning exit code
    else:
        return 0  # Success


def extract_test_names_and_covers(test_results: List[Dict]) -> List[Dict]:
    """
    Extract test names and covers information from parsed test results.

    This function is useful for validation and preview purposes.

    Args:
        test_results: List of parsed test results

    Returns:
        List[Dict]: List of extracted test information
    """
    extracted_tests = []

    for test_result in test_results:
        if test_result.get('type') == 'txt':
            scenarios = test_result.get('test_cases', [])

            for scenario in scenarios:
                if scenario.has_test_case():
                    # Structured scenario
                    covers_list = scenario.get_covers_list()

                    extracted_tests.append({
                        'test_name': scenario.get_test_case_name(),
                        'covers_list': covers_list,
                        'source_file': test_result.get('filename', 'Unknown'),
                        'type': 'structured_txt'
                    })
                elif scenario.has_raw_lines():
                    # Unstructured scenario
                    filename = test_result.get('filename', 'Unknown')
                    test_name = filename.replace('.txt', '') if filename.endswith('.txt') else filename
                    covers_list = scenario.get_covers_list()

                    extracted_tests.append({
                        'test_name': test_name,
                        'covers_list': covers_list,
                        'source_file': filename,
                        'type': 'unstructured_txt'
                    })

        elif test_result.get('type') == 'xml':
            content = test_result.get('content', {})
            filename = test_result.get('filename', 'Unknown')
            test_name = content.get('name', filename.replace('.xml', '') if filename.endswith('.xml') else filename)

            extracted_tests.append({
                'test_name': test_name,
                'covers_list': [],  # XML files don't have covers
                'source_file': filename,
                'type': 'xml'
            })

    return extracted_tests


def extract_test_name_from_scenario(scenario, filename: str) -> str:
    """
    Extract test name from a scenario using unified logic.

    Args:
        scenario: The scenario (UnitTestCaseData object or dictionary)
        filename: The filename for fallback

    Returns:
        str: The extracted test name
    """
    # Try structured scenario first
    if scenario.has_test_case():
        return scenario.get_test_case_name()

    # Try raw_lines scenario
    elif scenario.has_raw_lines():
        if hasattr(scenario, 'raw_lines') and scenario.raw_lines:
            for line in scenario.raw_lines:
                clean_line = line.strip()
                # Skip empty lines and covers lines
                if clean_line and not clean_line.lower().startswith('covers:'):
                    # Remove status indicators and use as test name
                    clean_test_name = re.sub(r'\s+[🟢🔴⚪]\s+(PASS|FAIL|SKIP)\s*$', '', clean_line).strip()
                    if clean_test_name:
                        return clean_test_name

    # Fallback to filename-based name
    return filename.replace('.txt', '') if filename.endswith('.txt') else filename


def validate_jama_environment_for_ut_creation(project_id: Optional[str] = None, test_set_id: Optional[str] = None, ut_test_case_id: Optional[str] = None) -> bool:
    """
    Validate that the Jama environment is properly configured for UT creation.

    Returns:
        bool: True if environment is valid, False otherwise
    """
    try:
        # Check environment variables
        if not validate_environment():
            return False

        # Try to initialize manager and validate test set
        jama_manager = JamaUTManager.get_instance()
        jama_manager.validate_test_set_exists()

        logging.info("Jama environment validation successful")
        return True

    except JamaConnectionError as e:
        logging.error(f"Jama environment validation failed: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error during environment validation: {e}")
        return False