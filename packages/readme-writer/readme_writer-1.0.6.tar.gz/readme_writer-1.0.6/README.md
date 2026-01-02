# README Writer

## Project Overview and Description

**readme-writer** is an AI-powered tool designed to automate the generation of comprehensive README files for software projects. By leveraging the OpenAI API, it analyzes code files to produce detailed documentation that adheres to best practices. This tool is particularly beneficial for developers aiming to streamline their documentation process, ensuring clarity and accessibility for both beginners and experienced developers.

## Installation Instructions

### Basic Installation

To install the `readme-writer` package, ensure you have Python 3.8 or later, then use the following command:

```bash
pip install -e .
```

### Development Installation

For development purposes, including additional dependencies:

```bash
pip install -e ".[dev]"
```

### Alternative Installation

Clone the repository and install the required dependencies:

```bash
git clone https://github.com/yourusername/readme-writer.git
cd readme-writer
pip install -e .
```

## Usage Examples and API Documentation

The `readme-writer` provides a command-line interface (CLI) for generating README files.

### Basic CLI Usage

```bash
readme-writer /path/to/repository --api-key YOUR_OPENAI_API_KEY
```

### Python Module Usage

To generate documentation using Python:

```python
from readme_writer.file_processor import FileProcessor
from readme_writer.config import Config
from pathlib import Path

config = Config()
processor = FileProcessor(config)
repository_path = Path('/path/to/your/repository')

files = processor.discover_files(repository_path)
files_with_content = processor.read_all_files(files)
documentation = processor.format_files_for_documentation(files_with_content)
```

### OpenAI Client Example

```python
from readme_writer.openai_client import OpenAIClient
from readme_writer.config import Config

config = Config()
client = OpenAIClient(config)

content = "Your content here"
system_prompt = "Generate a README section"
documentation = client.generate_documentation(content, system_prompt)
```

### CLI Options

- `repository_path`: Path to the Git repository (required).
- `--model`, `-m`: OpenAI model to use (default: `gpt-4o`).
- `--output`, `-o`: Output file name (default: `README.md`).
- `--api-key`: OpenAI API key (or set `OPENAI_API_KEY` environment variable).
- `--temperature`, `-t`: OpenAI temperature (default: `0.3`).
- `--skip-files`: Additional file patterns to skip (comma-separated).
- `--max-tokens`: Maximum tokens per chunk (default: `6000`).
- `--no-diff`: Disable diff analysis for detecting changes.

## Diff Analysis Feature

The `readme-writer` now includes intelligent diff analysis that detects changes between repository updates. This feature helps maintain accurate documentation by:

### What it detects:
- **Added files**: New files that should be documented
- **Deleted files**: Files that should be removed from documentation
- **Modified files**: Files that may need updated documentation

### How it works:
1. **Snapshot Creation**: When you run the tool, it creates a snapshot of the current repository state
2. **Change Detection**: On subsequent runs, it compares the current state with the previous snapshot
3. **Smart Updates**: The AI uses this change information to make targeted updates to your README

### Benefits:
- **Accurate Documentation**: Removes references to deleted files and adds documentation for new files
- **Efficient Updates**: Only updates sections that need changes, preserving existing content
- **Change Tracking**: Provides detailed information about what changed since the last update

### Usage:
```bash
# Normal usage with diff analysis (default)
readme-writer /path/to/repository

# Disable diff analysis if needed
readme-writer /path/to/repository --no-diff
```

### Snapshot Storage:
- Snapshots are stored in `.readme-writer-snapshots/` directory
- Each repository gets its own snapshot file
- Snapshots are automatically managed and updated

## Configuration Options and Environment Variables

The `readme-writer` can be configured using both CLI options and environment variables. Key configurations include:

- **Model Selection**: Choose the OpenAI model via the `--model` option or `OPENAI_MODEL` environment variable.
- **Output File**: Specify the output file with `--output` or `OUTPUT_FILE`.
- **API Key**: Set the OpenAI API key using `--api-key` or `OPENAI_API_KEY`.
- **Temperature**: Adjust the creativity of the AI with `--temperature`.

### Environment Variables

- `OPENAI_API_KEY`: API key for OpenAI services.
- `OPENAI_MODEL`: Default OpenAI model to use.
- `OUTPUT_FILE`: Default output file name.
- `VERSION`: Package version.

## Dependencies and Requirements

The project requires Python 3.8 or higher. Key dependencies include:

- `openai>=1.0.0`
- `click>=8.0.0`
- `tiktoken>=0.5.0`
- `rich>=13.0.0`
- `pyyaml>=6.0`
- `jinja2>=3.0.0`

## Contributing Guidelines

We welcome contributions to the `readme-writer` project. To contribute:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Ensure code quality with `black`, `flake8`, and `mypy`.
4. Write tests for your changes and ensure all tests pass.
5. Submit a pull request with a detailed description of your changes.

## GitHub Actions and PyPI Publishing

This project includes GitHub Actions workflows for automated testing and publishing to PyPI.

### Available Workflows

1. **Publish to PyPI** (`.github/workflows/publish.yml`):
   - Simple workflow for publishing to PyPI
   - Triggers on releases or manual dispatch

### Setting up PyPI Publishing

To enable automatic publishing to PyPI, you need to set up the following GitHub secret:

1. **PYPI_API_TOKEN**: Your PyPI API token
   - Go to [PyPI Account Settings](https://pypi.org/manage/account/)
   - Create an API token with "Entire account" scope
   - Add it as a repository secret named `PYPI_API_TOKEN`

### Publishing Methods

#### Method 1: GitHub Release
1. Create a new release on GitHub
2. Tag it with the version (e.g., `v1.0.1`)
3. The workflow will automatically publish to PyPI

#### Method 2: Manual Dispatch
1. Go to Actions tab in your repository
2. Select "Publish to PyPI"
3. Click "Run workflow"
4. Enter the version number (e.g., `1.0.1`)
5. Click "Run workflow"

### Version Management

The workflow automatically updates the version in `pyproject.toml` when publishing. Make sure to:
- Update the version in `pyproject.toml` before creating a release
- Use semantic versioning (e.g., `1.0.0`, `1.0.1`, `1.1.0`)

## Makefile Targets

The Makefile includes several useful commands:

- `install`: Install the package in development mode.
- `clean`: Clean build artifacts and cache.
- `build`: Build the package.
- `publish`: Build and publish to PyPI (requires proper configuration).
- `check-package`: Check the built package for issues.

## Important Notes and Considerations

- Ensure the OpenAI API key is set either via the environment variable or the CLI option to avoid errors during execution.
- The tool is in beta; expect potential changes and improvements.
- Proper configuration of the environment and dependencies is crucial for optimal performance.
- Monitor your API usage to manage expenses, as the tool estimates costs based on token usage.

For more detailed information, please refer to the individual file documentation and comments within the code.