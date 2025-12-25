# lupin_sw_ut_report

This project is a comprehensive software unit test reporting and management tool that processes test files and integrates with Jama for test lifecycle management. It converts test files (in `.txt` and `.xml` formats) into structured Markdown reports and provides advanced Jama integration for automated test case creation and result tracking.

## What This Tool Does

The `lupin_sw_ut_report` tool serves as a bridge between your test execution results and Jama test management system, providing three main capabilities:

### 1. Test File Processing and Report Generation
- **Parses Multiple Test Formats**: Processes both `.txt` files (with Given-When-Then format) and `.xml` files (JUnit-style test results)
- **Generates Structured Reports**: Creates comprehensive Markdown reports with test summaries, detailed test cases, and requirement coverage
- **Extracts Test Metadata**: Automatically extracts test names, status, dates, tags, and requirement IDs from test files
- **Supports Given-When-Then Format**: Specifically designed to parse and format BDD-style test scenarios with Given/When/Then/And steps

### 2. Jama Integration for Test Case Management
- **Automated Test Case Creation**: Creates unit test cases in Jama based on parsed test files
- **Module Organization**: Organizes tests by module in Jama folder structure
- **Requirement Linking**: Automatically links test cases to requirements using extracted requirement IDs
- **Status Management**: Updates test case statuses and workflow states in Jama
- **Dry-Run Capability**: Preview changes before applying them to Jama

### 3. Test Result Tracking and Reporting
- **Test Result Push**: Pushes test execution results to Jama test cycles
- **Version-Based Organization**: Organizes test results by software version
- **Test Plan Integration**: Creates and manages test plans and test cycles in Jama
- **Comprehensive Logging**: Provides detailed logging for debugging and audit trails

### 4. CI/CD Pipeline Integration
- **Automated Test Reporting**: Designed to run automatically in CI/CD pipelines (GitLab CI, Jenkins, GitHub Actions, etc.)
- **Version Tag Integration**: Automatically extracts version information from CI commit tags (`$CI_COMMIT_TAG`)
- **Pipeline Variable Support**: Seamlessly integrates with CI/CD environment variables and pipeline metadata
- **Exit Code Management**: Provides proper exit codes for pipeline success/failure detection
- **Headless Operation**: Runs without user interaction, perfect for automated environments
- **Configurable Logging**: Supports both console and file logging for pipeline artifact collection

## Key Features

- **Multi-Format Support**: Handles both TXT (BDD format) and XML (JUnit format) test files
- **Jama Cloud Integration**: Full integration with Jama Cloud for test management
- **Requirement Traceability**: Automatic linking of tests to requirements via ID extraction
- **Flexible Configuration**: Supports both command-line parameters and environment variables
- **CI/CD Pipeline Integration**: Built-in support for automated execution in CI/CD environments (GitLab CI, Jenkins, GitHub Actions)
- **Comprehensive Reporting**: Generates both Markdown and HTML reports
- **Error Handling**: Robust error handling with detailed logging and exit codes
- **Dry-Run Mode**: Safe testing of Jama operations without making changes

## Setting Up a Python Virtual Environment (Recommended for Development)

A **Python virtual environment** is an isolated workspace that allows you to install dependencies for a project without affecting your global Python installation or other projects. This is especially useful for development, as it helps avoid dependency conflicts and keeps your system clean.

> **Note:** This setup is recommended for developers who want to contribute to or test the project locally. End users installing via `pip install lupin-sw-ut-report` do not need to follow these steps.

### Why Use a Virtual Environment?

- Keeps project dependencies isolated from other Python projects and your system Python.
- Prevents version conflicts between packages.
- Makes it easy to manage and reproduce development environments.

### Step-by-Step Setup (Windows)

1. **Create a virtual environment in the project root:**

   ```powershell
   python -m venv .lupin_sw_ut_report
   ```

2. **Activate the virtual environment:**

   ```powershell
   .\.lupin_sw_ut_report\Scripts\activate
   ```

   You should see the environment name (e.g., `(.lupin_sw_ut_report)`) appear in your terminal prompt.

3. **Install the project in editable mode:**

   ```powershell
   pip install -e .
   ```

   This installs the project in "editable mode," meaning any changes you make to the source code will immediately affect your environment without needing to reinstall. This is ideal for development and testing.

4. **Deactivate the virtual environment when done:**

   ```powershell
   deactivate
   ```

   This returns your terminal to the global Python environment.

> **Tip:** The `.lupin_sw_ut_report` folder should be added to your `.gitignore` file to avoid committing it to version control.

## Installation

Run `pip install lupin-sw-ut-report`

## Basic Usage

This project provides a command-line interface to generate reports from a folder containing test files (`.txt` and `.xml`).

To run the script, use the following command:

```bash
sw-ut-report --input-folder <path/to/your/input-folder>
```

## Configuration

This project supports configuration through both command-line parameters and environment variables. **Command-line parameters take priority over environment variables**, which in turn take priority over default values.

### Priority Order

1. **Command-line parameters** (highest priority)
2. **Environment variables**
3. **Default values** (lowest priority)

## Command-Line Parameters

### Basic Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--input-folder` | string | Yes | Path to the folder containing the txt and xml files |
| `--version` | flag | No | Show version information and exit |

### Report Generation Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--markdown` | flag | True | Generate markdown report (default behavior) |
| `--no-markdown` | flag | False | Do not generate markdown report |

### Jama Integration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--create-ut` | flag | No | Create/update unit tests in Jama |
| `--module-name` | string | Yes* | Module name for Jama UT creation (required with --create-ut) |
| `--dry-run` | flag | False | Show what would be done without making changes to Jama |
| `--push-ut-test-results` | string | No | Push UT test results to Jama for the specified version |

### Jama Configuration Parameters

These parameters can be used to override environment variables for Jama integration:

| Parameter | Type | Description |
|-----------|------|-------------|
| `--jama-project-id` | string | Overrides `JAMA_DEFAULT_PROJECT_ID` environment variable |
| `--jama-test-set-id` | string | Overrides `JAMA_TEST_SET_ID` environment variable (default: "SmlPrep-SET-359") |
| `--jama-ut-test-case-id` | string | Overrides `JAMA_UT_TEST_CASE_ID` environment variable (default: "SmlPrep-UT-1") |
| `--jama-id-prefix` | string | Prefix to replace in covers fields (default: "SmlPrep") |

### CI/CD Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `--ci-commit-tag` | string | Pipeline GitLab variable $CI_COMMIT_TAG |

### Logging Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--log-level` | string | "INFO" | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `--log-file` | string | None | Path to log file (optional) |

## Complete Usage Examples

### Basic Report Generation

#### Generate Markdown Report Only

```bash
# Basic markdown generation
sw-ut-report --input-folder /path/to/test/files

# With custom logging
sw-ut-report --input-folder /path/to/test/files --log-level DEBUG

# Skip markdown generation (useful for Jama-only operations)
sw-ut-report --input-folder /path/to/test/files --no-markdown
```

### Jama Integration Examples

#### Create Unit Tests in Jama

```bash
# Basic UT creation
sw-ut-report --input-folder /path/to/test/files --create-ut --module-name "MyModule"

# Dry run to preview changes
sw-ut-report --input-folder /path/to/test/files --create-ut --module-name "MyModule" --dry-run

# With custom logging for debugging
sw-ut-report --input-folder /path/to/test/files --create-ut --module-name "MyModule" \
  --log-level DEBUG --log-file /path/to/jama-creation.log
```

#### Push Test Results to Jama

```bash
# Push results for a specific version
sw-ut-report --input-folder /path/to/test/files --push-ut-test-results "v1.2.3"

# With custom Jama configuration
sw-ut-report --input-folder /path/to/test/files --push-ut-test-results "v1.2.3" \
  --jama-project-id "8" --jama-test-set-id "MyProject-SET-123"
```

#### Override Jama Configuration

```bash
# Override all Jama settings
sw-ut-report --input-folder /path/to/test/files --create-ut --module-name "MyModule" \
  --jama-project-id "8" \
  --jama-test-set-id "MyProject-SET-123" \
  --jama-ut-test-case-id "MyProject-UT-456" \
  --jama-id-prefix "CustomPrefix"
```

### CI/CD Integration Examples

#### GitLab CI Pipeline

```bash
# With CI commit tag
sw-ut-report --input-folder /path/to/test/files --ci-commit-tag "$CI_COMMIT_TAG"

# Complete CI pipeline with Jama integration
sw-ut-report --input-folder /path/to/test/files \
  --create-ut \
  --module-name "$CI_PROJECT_NAME" \
  --ci-commit-tag "$CI_COMMIT_TAG" \
  --log-level INFO \
  --log-file "/tmp/ut-report-$CI_PIPELINE_ID.log"
```

### Advanced Configuration Examples

#### Multi-Environment Setup

```bash
# Development environment
sw-ut-report --input-folder /path/to/test/files --create-ut --module-name "MyModule" \
  --jama-id-prefix "DevProject" \
  --log-level DEBUG

# Production environment
sw-ut-report --input-folder /path/to/test/files --create-ut --module-name "MyModule" \
  --jama-id-prefix "ProdProject" \
  --log-level INFO
```

#### Comprehensive Workflow

```bash
# Complete workflow: generate report + create UTs + push results
sw-ut-report --input-folder /path/to/test/files \
  --create-ut \
  --module-name "MyModule" \
  --push-ut-test-results "v1.2.3" \
  --ci-commit-tag "v1.2.3" \
  --jama-project-id "8" \
  --jama-test-set-id "MyProject-SET-123" \
  --jama-ut-test-case-id "MyProject-UT-456" \
  --jama-id-prefix "MyProject" \
  --log-level INFO \
  --log-file "/var/log/ut-report.log"
```

### Troubleshooting Examples

#### Debug Mode

```bash
# Maximum debugging information
sw-ut-report --input-folder /path/to/test/files \
  --create-ut \
  --module-name "MyModule" \
  --dry-run \
  --log-level DEBUG \
  --log-file "/tmp/debug.log"
```

#### Validation Mode

```bash
# Validate configuration without making changes
sw-ut-report --input-folder /path/to/test/files \
  --create-ut \
  --module-name "MyModule" \
  --dry-run \
  --log-level INFO
```

## Environment Variables

This project supports several environment variables for configuration, particularly for Jama integration and sandbox environments.

### Jama Connection Variables (Required for Jama Integration)

| Variable | Required | Description |
|----------|----------|-------------|
| `JAMA_URL` | Yes | Your Jama instance URL |
| `JAMA_CLIENT_ID` | Yes | Your Jama client ID for authentication |
| `JAMA_CLIENT_PASSWORD` | Yes | Your Jama client password for authentication |
| `JAMA_DEFAULT_PROJECT_ID` | Yes | Default project ID for Jama operations |

### Jama Configuration Variables (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `JAMA_TEST_SET_ID` | "SmlPrep-SET-359" | Test set container for unit test organization |
| `JAMA_UT_TEST_CASE_ID` | "SmlPrep-UT-1" | Test case ID used for finding the UT test group |
| `JAMA_ID_PREFIX` | "SmlPrep" | Default prefix for ID replacement |
| `JAMA_PREFIXES_TO_REPLACE` | "SmlPrep" | Comma-separated list of prefixes to replace |


### Environment Variable Examples

#### Basic Jama Configuration

```bash
# Required Jama connection settings
export JAMA_URL="https://your-company.jamacloud.com"
export JAMA_CLIENT_ID="your-client-id"
export JAMA_CLIENT_PASSWORD="your-client-password"
export JAMA_DEFAULT_PROJECT_ID="8"
```

#### Custom Jama Configuration

```bash
# Optional: Custom test set and test case IDs
export JAMA_TEST_SET_ID="YourCustom-SET-123"
export JAMA_UT_TEST_CASE_ID="YourCustom-UT-456"

# Custom ID prefix
export JAMA_ID_PREFIX="MyProject"
export JAMA_PREFIXES_TO_REPLACE="SmlPrep,OldProject"
```

### Development Environment Setup Scripts

#### PowerShell Script (Windows)

Create a file named `setup-dev-env.ps1`:

```powershell
# Development Environment Setup Script for lupin_sw_ut_report
# Usage: .\setup-dev-env.ps1

Write-Host "Setting up development environment variables for lupin_sw_ut_report..." -ForegroundColor Green

# Required Jama connection settings (UPDATE THESE VALUES)
$env:JAMA_URL = "https://your-dev-company.jamacloud.com"
$env:JAMA_CLIENT_ID = "your-dev-client-id"
$env:JAMA_CLIENT_PASSWORD = "your-dev-client-password"
$env:JAMA_DEFAULT_PROJECT_ID = "8"

# Optional: Development-specific configuration
$env:JAMA_TEST_SET_ID = "DevProject-SET-123"
$env:JAMA_UT_TEST_CASE_ID = "DevProject-UT-456"
$env:JAMA_ID_PREFIX = "DevProject"
$env:JAMA_PREFIXES_TO_REPLACE = "SmlPrep,OldProject"

Write-Host "Environment variables set successfully!" -ForegroundColor Green
Write-Host "Jama URL: $env:JAMA_URL" -ForegroundColor Yellow
Write-Host "Project ID: $env:JAMA_DEFAULT_PROJECT_ID" -ForegroundColor Yellow
Write-Host "Test Set ID: $env:JAMA_TEST_SET_ID" -ForegroundColor Yellow

# Test the configuration
Write-Host "`nTesting configuration..." -ForegroundColor Cyan
sw-ut-report --version
```

## Logging Configuration

The application supports configurable logging through command-line parameters and environment variables.

### Log Levels

| Level | Description |
|-------|-------------|
| `DEBUG` | Detailed information for debugging |
| `INFO` | General information about program execution |
| `WARNING` | Warning messages for potential issues |
| `ERROR` | Error messages for serious problems |

### Logging CLI Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--log-level` | string | "INFO" | Set the logging level for console output |
| `--log-file` | string | None | Optional path to log file (enables file logging) |

### Logging Examples

```bash
# Debug logging to console only
sw-ut-report --input-folder /path/to/files --log-level DEBUG

# Info logging to both console and file
sw-ut-report --input-folder /path/to/files --log-level INFO --log-file /path/to/app.log

# Error logging to file only
sw-ut-report --input-folder /path/to/files --log-level ERROR --log-file /path/to/errors.log
```

### Log File Behavior

- When `--log-file` is specified, logs are written to both console and file
- File logging always uses DEBUG level for maximum detail
- Console logging uses the level specified by `--log-level`
- Log files are created if they don't exist
- Existing log files are appended to (not overwritten)

## Manual Publishing to PyPI

> **Note:**
> For a fully automated deployment process, see the next section on using the provided PowerShell script.

To publish this package to PyPI, follow these manual steps:

### 1. Update the Version

You must update the version number in **both** of these files:

- `src/sw_ut_report/__init__.py` (e.g., `__version__ = "0.1.0"`)
- `pyproject.toml` (e.g., `version = "0.1.0"`)

Make sure the version numbers match in both files. This is required for a successful and consistent release.

### 2. Build the Package

Install the build tool if you haven't already:

```bash
pip install build
```

Run the following command from the root of the project:

```bash
python -m build --no-isolation
```

This will generate distribution files in the `dist/` directory.

### 3. Prepare for Upload: PyPI Token and `.pypirc`

- Create an API token on your [PyPI account](https://pypi.org/manage/account/#api-tokens).
- Create a `.pypirc` file in the root of your repository (but **do not commit it to git**!).
- The `.pypirc` file is already listed in `.gitignore` by default, but always double-check before committing.

Example `.pypirc` file:

```ini
[distutils]
index-servers =
    pypi

[pypi]
username = __token__  # Do not change this value; it must remain exactly as shown
password = <your-pypi-api-token-here>  # Provide your token without any quotes or extra characters
```

**Replace `<your-pypi-api-token-here>` with your actual PyPI API token.**

- Do not add any quotation marks (`"` or `'`) or extra characters around the token.
- The line `username = __token__` must remain exactly as written.

> **Important:**
>
> - Never share your PyPI token.
> - Never commit `.pypirc` to version control, even if it is already in `.gitignore`.

### 4. Upload to PyPI

Install Twine if you haven't already:

```bash
pip install twine
```

Upload your package using Twine and your `.pypirc` configuration:

```bash
twine upload --config-file ./.pypirc dist/*
```

If successful, your package will be published to PyPI.

### Security Reminder

- Keep your PyPI API token secret.
- Do not share your `.pypirc` file or its contents.
- Always verify you are uploading the correct version and files.

### Automated Publishing with PowerShell

You can automate the version update, build, and upload process using the provided PowerShell script:

#### Prerequisites

- Windows with PowerShell 7 or later
- Python installed and available in your PATH
- `.pypirc` file present in the project root (see above for details)

#### Usage

From the project root, run:

```powershell
pwsh ./publish-to-pypi.ps1 -Version "0.1.2"
```

Replace `0.1.2` with your desired version number.

#### What the Script Does

- Checks for the presence of `.pypirc` and stops if missing
- Installs `build` and `twine` if not already installed
- Updates the version in both `src/sw_ut_report/__init__.py` and `pyproject.toml`
- Cleans the `dist/` directory
- Builds the package
- Uploads the package to PyPI using your `.pypirc` configuration
- Stops and reports at the first error

This script streamlines the release process and helps ensure consistency between your code and published package.
