import re
import xml.etree.ElementTree as ET
from datetime import datetime
from os import PathLike
from typing import Dict, Optional, Tuple

from sw_ut_report.constants import FAIL, NA, PASS
from sw_ut_report.parse_txt_file import Requirement, SummaryRequirementsStatus
from sw_ut_report.utils import remove_excess_space, apply_jama_prefix_replacement


def _format_testcase_name(testcase: ET.Element) -> str:
    testcase_name = remove_excess_space(testcase.attrib.get("name")).replace("::", ": ")
    testcase_name_split = testcase_name.split(":")
    if len(testcase_name_split) > 1:
        testcase_name = (
            f"**{testcase_name_split[0].strip()}**: {','.join(testcase_name_split[1:])}"
        )
    return testcase_name.strip()


def _extract_requirement_id(testcase_name: str) -> Optional[str]:
    requirement_pattern = r"(?:SmlPrep-)?SUBSR-\d+"
    match = re.search(requirement_pattern, testcase_name)

    if match:
        return match.group()
    return None


def _add_requirement_to_summary(
    testcase_name: str, status_test: str, summary: SummaryRequirementsStatus
):
    requirement_id = _extract_requirement_id(testcase_name)
    if requirement_id:
        # Apply jama_id_prefix_replacement for consistency with TXT files
        requirement_id = apply_jama_prefix_replacement(requirement_id)
        summary.add_requirement(Requirement(id=requirement_id, status=status_test))


def _get_formatted_timestamp(testsuites_id: str) -> str:
    try:
        timestamp = datetime.strptime(testsuites_id, "%Y %m %d %H:%M:%S")
        formatted_timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        formatted_timestamp = testsuites_id
    return formatted_timestamp


def _if_failures(testsuites_failures: str) -> str:
    return FAIL if int(testsuites_failures) > 0 else PASS


def format_xml_to_dict(
    xml_file: PathLike, summary: SummaryRequirementsStatus
) -> Tuple[Dict, SummaryRequirementsStatus]:
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Extract information from the first level "testsuites"
    testsuites_name = root.attrib.get("name")
    testsuites_id = root.attrib.get("id")
    testsuites_tests = root.attrib.get("tests")
    testsuites_errors = root.attrib.get("errors")
    testsuites_failures = root.attrib.get("failures")

    testsuites_status = _if_failures(testsuites_failures)

    # Add the test results to the summary
    # Apply jama_id_prefix_replacement for consistency with TXT files
    processed_testsuites_name = apply_jama_prefix_replacement(testsuites_name)

    summary.add_requirement(
        Requirement(
            id=processed_testsuites_name,
            status=testsuites_status,
        )
    )

    testsuites_dict = {
        "name": testsuites_name,
        "timestamp": _get_formatted_timestamp(testsuites_id),
        "tests": testsuites_tests,
        "errors": testsuites_errors,
        "failures": testsuites_failures,
        "status": testsuites_status,
        "suites": [],
    }

    # Browse each "testsuite" in "testsuites"
    for testsuite in root.findall("testsuite"):
        testsuite_name = testsuite.attrib.get("name")
        testsuite_tests = testsuite.attrib.get("tests")
        testsuite_failures = testsuite.attrib.get("failures")
        status_suite = _if_failures(testsuite_failures)

        testsuite_dict = {
            "name": testsuite_name,
            "tests": testsuite_tests,
            "failures": testsuite_failures,
            "status": status_suite,
            "testcases": [],
        }

        # Browse each "testcase" in "testsuite"
        for testcase in testsuite.findall("testcase"):
            testcase_name = _format_testcase_name(testcase)
            testcase_tests = testcase.attrib.get("tests", "N/A")
            testcase_failures = testcase.attrib.get("failed", "N/A")
            if testcase_failures == "N/A":
                status_test = NA
            else:
                status_test = _if_failures(testcase_failures)

            testcase_dict = {
                "name": testcase_name,
                "tests": testcase_tests,
                "failures": testcase_failures,
                "status": status_test,
            }
            testsuite_dict["testcases"].append(testcase_dict)
            _add_requirement_to_summary(testcase_name, status_test, summary)

        testsuites_dict["suites"].append(testsuite_dict)
    return testsuites_dict, summary
