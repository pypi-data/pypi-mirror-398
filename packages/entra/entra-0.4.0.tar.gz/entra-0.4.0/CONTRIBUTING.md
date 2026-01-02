# Contributing to entra

Thank you for your interest in contributing to entra! This document provides guidelines and instructions for contributing.

## Ways to Contribute

- **Bug Reports**: Open an issue describing the bug, including steps to reproduce
- **Feature Requests**: Open an issue describing the feature and its use case
- **Code Contributions**: Submit a pull request with your changes
- **Documentation**: Improve README, docstrings, or add examples

## Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/entra.git
   cd entra
   ```

2. Create a virtual environment and install in development mode:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[testing]"
   ```

3. Run tests to verify your setup:
   ```bash
   pytest
   ```

## Pull Request Process

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, following the code style of the project

3. Add tests for any new functionality

4. Ensure all tests pass:
   ```bash
   pytest --cov=entra
   ```

5. Commit your changes with a descriptive message

6. Push to your fork and submit a pull request

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to public functions and classes
- Keep functions focused and modular

## Testing

- Write tests for new features
- Maintain or improve code coverage
- Tests are run with pytest

## Questions?

If you have questions, feel free to open an issue or reach out to the maintainers.
