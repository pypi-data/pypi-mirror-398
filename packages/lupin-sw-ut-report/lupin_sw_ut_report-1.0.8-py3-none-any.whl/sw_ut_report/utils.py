import logging
import re
from os import PathLike
from typing import Dict, List, Optional

from sw_ut_report.constants import FILE_NAME
from sw_ut_report.template_manager import get_local_template


def apply_jama_prefix_replacement(text: str) -> str:
    """
    Apply search and replace for Jama ID prefixes.

    This is the single, centralized function for all jama prefix replacements.

    Args:
        text: The text to process

    Returns:
        str: The text with prefixes replaced
    """
    if not text:
        return text

    try:
        from sw_ut_report.config import GlobalConfig
        return GlobalConfig.apply_jama_id_prefix_replacement(text)
    except (ImportError, RuntimeError):
        # Fallback if GlobalConfig is not available or not initialized
        return text


def remove_excess_space(line: str) -> str:
    return " ".join(line.split())


def extract_tag(filename: str) -> Optional[str]:
    try:
        first_dot_index = filename.find(".")
        if first_dot_index == -1:
            return None

        # Find the last underscore before the first dot to mark the start of the tag
        start_index = filename.rfind("_", 0, first_dot_index) + 1

        # Find the first underscore after the first dot to mark the end of the tag
        end_index = filename.find("_", first_dot_index)
        if end_index == -1:
            return None

        return filename[start_index:end_index]

    except Exception as e:
        logging.error(f"Error extracting tag: {e}")
        return None


def extract_date(filename: str) -> Optional[str]:
    date_match = re.search(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}", filename)
    date = date_match.group(0) if date_match else None
    return date


def extract_tag_date_and_clean_filename(filename: str):
    tag = extract_tag(filename)
    date = extract_date(filename)

    cleaned_filename = filename
    if tag is not None:
        cleaned_filename = cleaned_filename.replace(f"_{tag}", "")
    if date is not None:
        cleaned_filename = cleaned_filename.replace(f"_{date}", "")

    # Escape underscores for the final output for pdf conversion
    cleaned_filename = cleaned_filename.replace("_", "\\_")
    return tag, date, cleaned_filename


def read_file_content(input_file: PathLike) -> str:
    with open(input_file, "r", encoding="utf-8") as f:
        return f.read()


def generate_single_markdown(
    reports: List[Dict], summary, ci_commit_tag: Optional[str]
) -> None:
    template = get_local_template("combined_test_report.j2")

    title = "Lupin Automatic Software Unit Tests Result"
    file_name = f"{FILE_NAME}.md"
    if ci_commit_tag:
        file_name = f"{FILE_NAME}_{ci_commit_tag}.md"
        title = f"{title} {ci_commit_tag}"

    markdown_content = template.render(reports=reports, summary=summary, title=title)

    with open(file_name, "w", encoding="utf-8") as md_file:
        md_file.write(markdown_content)
