import re
from typing import List, Tuple

from sw_ut_report.constants import FAIL, PASS
from sw_ut_report.unit_test_case_data import (
    Requirement,
    SummaryRequirementsStatus,
    UnitTestCaseData,
)
from sw_ut_report.utils import remove_excess_space, apply_jama_prefix_replacement


def _split_covers_line(line: str) -> List[str]:
    line = re.sub(r"Covers:\s*", "", line).strip()
    # Apply search and replace for Jama ID prefixes
    line = apply_jama_prefix_replacement(line)
    return re.findall(r"\[([^\]]+)\]", line)


def _format_given_when_then(line: str, prefix: str) -> str:
    line = line.split(": ", 1)[1].strip()
    if line.lower().startswith(prefix):
        line = line.lower().replace(prefix, "").strip()
    formatted_line = f"**{prefix.capitalize()}**: {line}"
    return formatted_line


def _create_segments(lines: List[str]) -> List[List[str]]:
    """Crée les segments de UnitTestCaseData à partir des lignes du fichier."""
    segments = []
    current_segment = []

    for i in range(len(lines) - 1):
        line = lines[i].strip()
        next_line = lines[i + 1].strip().lower()

        # Début d'un nouveau `UnitTestCaseData` segment si la ligne n'est pas vide et est suivie par "Covers:"
        if line and next_line.startswith("covers:"):
            if current_segment:
                segments.append(current_segment)
            current_segment = [line, lines[i + 1]]
        elif current_segment:
            # Ajouter les lignes au segment en cours
            current_segment.append(line)

    # Ajouter le dernier segment s'il existe
    if current_segment:
        segments.append(current_segment)

    return segments


def _process_segments(
    segments: List[List[str]], summary_requirements: SummaryRequirementsStatus
) -> List[UnitTestCaseData]:
    """Process each segment to create `UnitTestCaseData` instances.

    Args:
        segments (List[List[str]]): List of segments where each segment contains lines of a `UnitTestCaseData`.
        summary_requirements (SummaryRequirementsStatus): Summary of requirements status.

    Returns:
        List[UnitTestCaseData]: List of `UnitTestCaseData` instances."""
    test_cases = []

    for segment in segments:
        # The first two lines of the segment are scenario and covers line
        scenario_line = segment[0].strip()
        covers_line = segment[1].strip()

        scenario = scenario_line
        scenario_status = PASS if scenario_line.lower().endswith("pass") else FAIL

        current_case = UnitTestCaseData(
            scenario=scenario,
            scenario_status=scenario_status,
            requirements_covers=[],
            given_when_then=[],
            additional_tests=[],
        )

        # Extract requirements from the covers line
        split_requirements = _split_covers_line(covers_line)
        current_case.requirements_covers.extend(
            Requirement(req, "Not covered") for req in split_requirements
        )

        # Extract `Given`, `When`, `Then` and `And` steps
        current_block = []
        for line in segment[2:]:
            cleaned_line = line.strip().lower()

            if cleaned_line.startswith("given:"):
                if current_block:
                    current_case.given_when_then.append(current_block)

                current_block = [_format_given_when_then(line, "given")]

            elif cleaned_line.startswith("when:"):
                current_block.append(_format_given_when_then(line, "when"))

            elif cleaned_line.startswith("then:"):
                current_block.append(_format_given_when_then(line, "then"))

            elif cleaned_line.startswith("and:"):
                current_block.append(_format_given_when_then(line, "and"))

            elif cleaned_line and not cleaned_line.startswith("covers:"):
                # Add additional tests lines who are not empty and not starts with "Covers:"
                current_case.additional_tests.append(line.strip())

        if current_block:
            current_case.given_when_then.append(current_block)

        current_case.update_requirements_status(summary_requirements)
        test_cases.append(current_case)

    return test_cases


def generate_test_cases(
    file_content: str, summary: SummaryRequirementsStatus
) -> Tuple[List[UnitTestCaseData], SummaryRequirementsStatus]:
    lines = file_content.splitlines()
    lines = [remove_excess_space(line) for line in lines]

    segments = _create_segments(lines)

    test_cases = _process_segments(segments, summary)

    return test_cases, summary
