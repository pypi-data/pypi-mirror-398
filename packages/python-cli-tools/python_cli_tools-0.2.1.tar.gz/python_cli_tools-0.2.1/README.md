# Python CLI Tools

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
![Tests](https://github.com/wrogistefan/python-cli-tools/actions/workflows/tests.yml/badge.svg)
[![codecov](https://codecov.io/gh/wrogistefan/python-cli-tools/branch/main/graph/badge.svg)](https://codecov.io/gh/wrogistefan/python-cli-tools)

A collection of practical, well-tested command-line utilities implemented in Python. This project demonstrates modular CLI tool development with a clean `src/` layout, comprehensive testing, and easy distribution via PyPI.

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Tools](#tools)
  - [File Organizer](#file-organizer)
  - [Password Generator](#password-generator)
  - [Weather CLI](#weather-cli)
- [Testing](#testing)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

## Features

- **Modular Design**: Each tool is isolated in its own package under `src/`, promoting maintainability and reusability.
- **Comprehensive Testing**: Unit tests with `pytest` ensure reliability and facilitate refactoring.
- **Console Scripts**: Tools are installable as command-line scripts via `pyproject.toml`.
- **Minimal Dependencies**: Only essential libraries are used, with `requests` for network operations.
- **Cross-Platform**: Compatible with Windows, macOS, and Linux.
- **Open Source**: Licensed under MIT, encouraging contributions and modifications.

## Project Structure

```
python-cli-tools/
├── src/
│   ├── file_organizer/
│   │   ├── __init__.py
│   │   └── file_organizer.py
│   ├── password_generator/
│   │   ├── __init__.py
│   │   └── password_generator.py
│   └── weather_cli/
│       ├── __init__.py
│       └── weather_cli.py
├── tests/
│   ├── __init__.py
│   ├── test_file_organizer.py
│   ├── test_password_generator.py
│   └── test_weather_cli.py
├── docs/
│   └── usage_examples.md
├── .github/
│   └── workflows/
│       └── tests.yml
├── CHANGELOG.md
├── LICENSE
├── README.md
├── pyproject.toml
├── requirements.txt
└── .gitignore
```

## Installation

### Prerequisites

- Python 3.10 or higher
- `pip` for package management

### Quick Install

1. Clone the repository:
   ```bash
   git clone https://github.com/wrogistefan/python-cli-tools.git
   cd python-cli-tools
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # On Windows (PowerShell)
   .venv\Scripts\Activate.ps1
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. Install dependencies and the package in editable mode:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

This installs the tools as console scripts: `file-organizer`, `password-generator`, and `weather-cli`.

## Usage

After installation, run the tools directly from the command line:

```bash
file-organizer <directory>
password-generator
weather-cli --city "New York"
```

Alternatively, run as Python modules:

```bash
python -m file_organizer.file_organizer <directory>
python -m password_generator.password_generator
python -m weather_cli.weather_cli --city "New York"
```

## Tools

### File Organizer

Organizes files in a specified directory into subdirectories based on their file extensions.

**Usage:**
```bash
file-organizer <directory>
```

**Example:**
```bash
file-organizer ./downloads
```

**Sample Output:**
```
Moved: report.pdf -> ./downloads/pdf
Moved: photo.jpg -> ./downloads/jpg
Moved: README -> ./downloads/no_extension
```

**Source:** [`src/file_organizer/file_organizer.py`](src/file_organizer/file_organizer.py)

### Password Generator

Generates secure, customizable random passwords with options for length and character sets.

**Usage:**
```bash
password-generator [options]
```

**Options:**
- `-l, --length`: Specify password length (default: 12)
- `--no-digits`: Exclude digits
- `--no-specials`: Exclude special characters

**Examples:**
```bash
password-generator
password-generator -l 16 --no-specials
```

**Sample Output:**
```
k9F3nAq2Zo1LmV7$
```

**Source:** [`src/password_generator/password_generator.py`](src/password_generator/password_generator.py)

### Weather CLI

Fetches and displays real-time weather data for a specified location using the Open-Meteo API.

**Usage:**
```bash
weather-cli --city <city_name>
weather-cli --lat <latitude> --lon <longitude>
```

**Examples:**
```bash
weather-cli --city "New York"
weather-cli --lat 37.075 --lon 15.286
```

**Sample Output:**
```
📍 Location: Syracuse, Italy (37.07542, 15.28664)

🌤️  Current Weather:
   🌡️  Temperature: 12.9°C
   💨  Wind Speed: 2.5 km/h
   🧭  Wind Direction: 270°
   ⏱️  Observation Time: 2025-12-25T17:45
```

**Source:** [`src/weather_cli/weather_cli.py`](src/weather_cli/weather_cli.py)

For more detailed examples, see [`docs/usage_examples.md`](docs/usage_examples.md).

## Testing

Run the test suite using `pytest`:

```bash
pytest
```

Tests are located in the `tests/` directory and cover all tools to ensure functionality and prevent regressions.

## Development

### Building for Distribution

To build wheel and source distributions:

```bash
pip install build
python -m build
```

Artifacts will be created in the `dist/` directory.

### Code Quality

- Use `black` for code formatting (configured in `pyproject.toml`).
- Follow PEP 8 style guidelines.
- Maintain high test coverage.

### Adding New Tools

1. Create a new package under `src/`.
2. Implement the tool in a module with a `main()` function.
3. Add console script entry in `pyproject.toml`.
4. Write comprehensive tests in `tests/`.
5. Update documentation.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature-name`.
3. Write tests for new functionality.
4. Ensure all tests pass: `pytest`.
5. Commit your changes: `git commit -m 'Add some feature'`.
6. Push to the branch: `git push origin feature/your-feature-name`.
7. Open a pull request.

Please read the [contributing guidelines](CONTRIBUTING.md) if available, and ensure your code adheres to the project's standards.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Łukasz Perek**

This project serves as a portfolio piece demonstrating practical CLI development, modular Python packaging, and the transition into software engineering and AI freelancing.
