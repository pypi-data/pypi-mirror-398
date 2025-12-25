import re
from dataclasses import dataclass, field
from typing import List

from sw_ut_report.constants import FAIL, PASS


@dataclass
class Requirement:
    id: str
    status: str


@dataclass
class SummaryRequirementsStatus:
    summary: List[Requirement] = field(default_factory=list)

    def __post_init__(self):
        self._requirements_dict = {req.id: req for req in self.summary}

    def add_requirement(self, new_requirement: Requirement):
        existing_requirement = self._requirements_dict.get(new_requirement.id)

        if existing_requirement:
            if existing_requirement.status == PASS and new_requirement.status == FAIL:
                existing_requirement.status = FAIL
        else:
            self.summary.append(new_requirement)
            self._requirements_dict[new_requirement.id] = new_requirement

    def sort_summary(self):
        def sort_key(req: Requirement):
            match = re.search(r"(\d+)$", req.id)
            number = int(match.group(1)) if match else float("inf")
            return (req.id[: match.start()] if match else req.id, number)

        self.summary.sort(key=sort_key)


@dataclass
class UnitTestCaseData:
    scenario: str
    scenario_status: str
    requirements_covers: List[Requirement]
    given_when_then: List[List[str]] = field(default_factory=list)
    additional_tests: List[str] = field(default_factory=list)

    def update_requirements_status(
        self, summary_requirements: SummaryRequirementsStatus
    ):
        for requirement in self.requirements_covers:
            requirement.status = PASS if self.scenario_status == PASS else FAIL
            summary_requirements.add_requirement(requirement)

    def get_covers_list(self) -> List[str]:
        """Get list of requirement IDs."""
        return [req.id for req in self.requirements_covers]

    def get_test_case_name(self) -> str:
        """Get test case name."""
        return self.scenario

    def has_raw_lines(self) -> bool:
        """Check if this scenario has raw lines (for unstructured scenarios)."""
        return False  # UnitTestCaseData doesn't have raw lines

    def get_steps(self) -> List[dict]:
        """Convert given_when_then to steps format expected by other modules."""
        steps = []
        for block in self.given_when_then:
            step = {}
            for line in block:
                if line.lower().startswith('**given**:'):
                    step['given'] = line.replace('**Given**:', '').strip()
                elif line.lower().startswith('**when**:'):
                    step['when'] = line.replace('**When**:', '').strip()
                elif line.lower().startswith('**then**:'):
                    step['then'] = line.replace('**Then**:', '').strip()
            if step:  # Only add if step has content
                steps.append(step)
        return steps

    def has_test_case(self) -> bool:
        """Check if this scenario has a test case (structured scenario)."""
        return True  # UnitTestCaseData always has a test case (scenario)

    def has_steps(self) -> bool:
        """Check if this scenario has steps."""
        return len(self.given_when_then) > 0