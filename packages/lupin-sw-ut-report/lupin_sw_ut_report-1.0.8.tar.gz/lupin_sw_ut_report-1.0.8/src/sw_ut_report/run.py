import os
import sys
from typing import Optional

import typer

from sw_ut_report.__init__ import __version__
from sw_ut_report.parse_txt_file import SummaryRequirementsStatus, generate_test_cases
from sw_ut_report.parse_xml_file import format_xml_to_dict
# Jama imports will be loaded conditionally when needed
from sw_ut_report.utils import (
    extract_tag_date_and_clean_filename,
    generate_single_markdown,
    read_file_content,
)

cli = typer.Typer()


def input_folder_option() -> typer.Option:
    return typer.Option(
        ...,
        "--input-folder",
        help="Path to the folder containing the txt and xml files",
    )


def ci_commit_tag_option() -> typer.Option:
    return typer.Option(
        None,
        "--ci-commit-tag",
        help="Pipeline GitLab variable $CI_COMMIT_TAG",
    )


def version_callback(value: bool):
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@cli.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", callback=version_callback, is_flag=True, is_eager=True
    ),
    input_folder: str = input_folder_option(),
    generate_markdown: bool = typer.Option(True, "--markdown", help="Generate markdown report"),
    no_markdown: bool = typer.Option(False, "--no-markdown", help="Do not generate markdown report"),
    create_jama_ut: bool = typer.Option(False, "--create-ut", help="Create/update unit tests in Jama"),
    module_name: Optional[str] = typer.Option(None, "--module-name", help="Module name for Jama UT creation (required with --create-ut)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done without making changes to Jama"),
    push_ut_test_results: Optional[str] = typer.Option(None, "--push-ut-test-results", help="Push UT test results to Jama for the specified version"),
    jama_project_id: Optional[str] = typer.Option(None, "--jama-project-id", help="Jama project ID (overrides JAMA_DEFAULT_PROJECT_ID environment variable)"),
    jama_test_set_id: Optional[str] = typer.Option(None, "--jama-test-set-id", help="Jama test set ID (overrides JAMA_TEST_SET_ID environment variable)"),
    jama_ut_test_case_id: Optional[str] = typer.Option(None, "--jama-ut-test-case-id", help="Jama UT test case ID (overrides JAMA_UT_TEST_CASE_ID environment variable)"),
    jama_id_prefix: Optional[str] = typer.Option("SmlPrep", "--jama-id-prefix", help="Prefix to replace in covers fields (default: SmlPrep)"),
    ci_commit_tag: str = ci_commit_tag_option(),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level (DEBUG, INFO, WARNING, ERROR)"),
    log_file: Optional[str] = typer.Option(None, "--log-file", help="Path to log file (optional)"),
):
    # Vérification explicite de --version AVANT tout autre traitement
    # Ceci garantit que la version s'affiche même si le callback is_eager ne fonctionne pas dans certains environnements

    # Initialize logging early for debug messages
    from sw_ut_report.jama_common import setup_logging
    import logging

    # Convert string log level to logging constant for console
    console_level = getattr(logging, log_level.upper(), logging.INFO)
    setup_logging(console_level=console_level, log_file=log_file, file_level=logging.DEBUG)

    # Logs de débogage pour tracer les paramètres reçus
    logging.debug(f"version = {version}")
    logging.debug(f"input_folder = {input_folder}")
    logging.debug(f"generate_markdown = {generate_markdown}")
    logging.debug(f"no_markdown = {no_markdown}")
    logging.debug(f"create_jama_ut = {create_jama_ut}")
    logging.debug(f"module_name = {module_name}")
    logging.debug(f"dry_run = {dry_run}")
    logging.debug(f"push_ut_test_results = {push_ut_test_results}")
    logging.debug(f"jama_project_id = {jama_project_id}")
    logging.debug(f"jama_test_set_id = {jama_test_set_id}")
    logging.debug(f"jama_ut_test_case_id = {jama_ut_test_case_id}")
    logging.debug(f"jama_id_prefix = {jama_id_prefix}")
    logging.debug(f"ctx.invoked_subcommand = {ctx.invoked_subcommand}")

    if version is True:
        typer.echo(__version__)
        sys.exit(0)

    if ctx.invoked_subcommand is None:
        # Si input_folder est None, ne pas traiter la génération de rapports
        if input_folder is None:
            logging.error("--input-folder is required for report generation")
            raise typer.Exit(code=1)

        # Handle markdown generation logic
        if no_markdown:
            generate_markdown = False

        # Update global configuration with CLI arguments
        from sw_ut_report.jama_common import JamaUTManager
        JamaUTManager.update_global_config(jama_project_id, jama_test_set_id, jama_ut_test_case_id, jama_id_prefix)

        generate_report(input_folder, generate_markdown, create_jama_ut, module_name, dry_run, push_ut_test_results, jama_project_id, jama_test_set_id, jama_ut_test_case_id, ci_commit_tag, log_level, log_file)


def generate_report(
    input_folder: str,
    generate_markdown: bool,
    create_jama_ut: bool,
    module_name: Optional[str],
    dry_run: bool,
    push_ut_test_results: Optional[str],
    jama_project_id: Optional[str],
    jama_test_set_id: Optional[str],
    jama_ut_test_case_id: Optional[str],
    ci_commit_tag: Optional[str],
    log_level: str = "INFO",
    log_file: Optional[str] = None
):
    # Logging is already initialized in main()
    import logging

    # Validate parameters
    if input_folder is None:
        logging.error("--input-folder is required for report generation")
        raise typer.Exit(code=1)


    if create_jama_ut and not module_name:
        logging.error("--module-name is required when --create-ut is used")
        raise typer.Exit(code=1)

    if push_ut_test_results is not None and push_ut_test_results.strip() and not input_folder:
        logging.error("--input-folder is required when --push-ut-test-results is used")
        raise typer.Exit(code=1)

    if not generate_markdown and not create_jama_ut and not (push_ut_test_results is not None and push_ut_test_results.strip()):
        logging.error("At least one output option must be specified (--markdown, --create-ut, or --push-ut-test-results)")
        raise typer.Exit(code=1)

    # Dry-run validation
    if dry_run and not create_jama_ut:
        logging.info("--dry-run only applies to Jama operations. Use with --create-ut to see Jama actions.")

    # Handle push UT test results first
    if push_ut_test_results is not None and push_ut_test_results.strip():
        logging.info(f"Pushing UT test results to Jama for version: {push_ut_test_results}")

        try:
            # Load Jama modules only when needed
            from sw_ut_report.jama_common import JamaConnectionError, JamaValidationError
            from sw_ut_report.push_ut_test_results import push_ut_test_results_to_jama

            ut_result = push_ut_test_results_to_jama(push_ut_test_results, input_folder, jama_project_id, jama_test_set_id, jama_ut_test_case_id)

            if ut_result == 0:
                logging.info("Successfully pushed UT test results to Jama")
                raise typer.Exit(code=0)
            elif ut_result == 1:
                logging.error("Failed to push UT test results to Jama")
                raise typer.Exit(code=1)
            elif ut_result == 2:
                logging.warning("Pushed UT test results to Jama with warnings")
                raise typer.Exit(code=2)
            else:
                logging.error(f"Failed to push UT test results to Jama (unknown result: {ut_result})")
                raise typer.Exit(code=1)

        except (JamaConnectionError, JamaValidationError) as e:
            logging.error(f"Jama operation failed: {e}")
            raise typer.Exit(code=1)
        except typer.Exit:
            # Re-raise typer.Exit to preserve the original exit code
            raise
        except Exception as e:
            logging.error(f"Error pushing UT test results: {e}")
            raise typer.Exit(code=1)
        return

    logging.info("Test reports generation started")

    reports = []
    summary_requirements = SummaryRequirementsStatus()

    try:
        file_list = os.listdir(input_folder)
    except FileNotFoundError:
        logging.error(f"Path '{input_folder}' does not exist.")
        raise typer.Exit(code=1)
    except PermissionError:
        logging.error(f"Permission denied for the folder '{input_folder}'.")
        raise typer.Exit(code=1)

    for filename in file_list:
        input_file = os.path.join(input_folder, filename)
        _, file_extension = os.path.splitext(filename)

        tag, date, clean_filename = extract_tag_date_and_clean_filename(filename)
        match file_extension.lower():
            case ".txt":
                test_cases, summary_requirements = generate_test_cases(
                    read_file_content(input_file), summary_requirements
                )
                reports.append(
                    {
                        "type": "txt",
                        "filename": clean_filename,
                        "tag": tag,
                        "date": date,
                        "test_cases": test_cases,
                    }
                )

            case ".xml":
                suites_data, summary_requirements = format_xml_to_dict(
                    input_file, summary_requirements
                )
                reports.append(
                    {
                        "type": "xml",
                        "filename": clean_filename,
                        "tag": tag,
                        "date": date,
                        "content": suites_data,
                    }
                )

            case _:
                if os.path.isdir(input_file):
                    logging.info(f"Skipping folder: {filename}")
                    continue
                else:
                    logging.info(f"Skipping unsupported file format: {filename}")
                    continue

    if not reports:
        logging.warning("No test files found to process.")
        return



    # Execute requested operations
    exit_code = 0  # Default success code

    # Create UTs in Jama if requested
    if create_jama_ut:
        try:
            # Load Jama modules only when needed
            from sw_ut_report.jama_common import JamaConnectionError, JamaValidationError

            if dry_run:
                from sw_ut_report.jama_ut_manager import dry_run_unit_tests_creation

                logging.info(f"DRY-RUN: Analyzing what would be done for module: {module_name}")
                logging.info("=" * 60)

                ut_result = dry_run_unit_tests_creation(module_name, reports, jama_project_id, jama_test_set_id, jama_ut_test_case_id)

                if ut_result == 0:
                    logging.info("Dry-run analysis completed successfully")
                    exit_code = 0
                elif ut_result == 1:
                    logging.error("Dry-run analysis found errors")
                    exit_code = 1
                elif ut_result == 2:
                    logging.warning("Dry-run analysis completed with warnings")
                    exit_code = 2
                else:
                    logging.error("Dry-run analysis failed")
                    exit_code = 1

            else:
                from sw_ut_report.jama_ut_manager import create_unit_tests_in_jama

                logging.info(f"Creating/updating unit tests in Jama for module: {module_name}")
                logging.info("=" * 60)

                ut_result = create_unit_tests_in_jama(module_name, reports, jama_project_id, jama_test_set_id, jama_ut_test_case_id)

                if ut_result == 0:
                    logging.info("Successfully created/updated unit tests in Jama")
                    exit_code = 0
                elif ut_result == 1:
                    logging.error("Failed to create/update unit tests in Jama")
                    exit_code = 1
                elif ut_result == 2:
                    logging.warning("Created/updated unit tests in Jama with warnings")
                    exit_code = 2
                else:
                    logging.error("Failed to create/update unit tests in Jama")
                    exit_code = 1

        except (JamaConnectionError, JamaValidationError) as e:
            logging.error(f"Jama operation failed: {e}")
            exit_code = 1
        except typer.Exit:
            # Re-raise typer.Exit to preserve the original exit code
            raise
        except Exception as e:
            logging.error(f"Unexpected error during Jama operations: {e}")
            exit_code = 1

        # Exit with the appropriate code for Jama operations
        logging.info(f"Exit code: {exit_code}")
        raise typer.Exit(code=exit_code)

    # Generate markdown report if requested
    if generate_markdown:
        try:
            summary_requirements.sort_summary()
            generate_single_markdown(reports, summary_requirements.summary, ci_commit_tag)
            logging.info("Successfully generated markdown report")
            # Keep exit_code as 0 for success
        except Exception as e:
            logging.error(f"Failed to generate markdown report: {e}")
            exit_code = 1

    # Final exit with the determined code
    logging.info(f"Final exit code: {exit_code}")
    raise typer.Exit(code=exit_code)
