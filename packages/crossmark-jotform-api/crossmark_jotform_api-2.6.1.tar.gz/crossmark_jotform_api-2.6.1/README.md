<div align="center"><img src="https://raw.githubusercontent.com/mirkan1/crossmark-jotform-api/master/logo.png" alt="" height="150"></div>

# CROSSMARK JOTFORM API

Reason of this library is to provide a simple and easy-to-use interface for interacting with the JotForm API. It is designed to be used by developers who want to integrate JotForm functionality into their applications.

[![PyPI version](https://badge.fury.io/py/crossmark-jotform-api.svg)](https://badge.fury.io/py/crossmark-jotform-api)
[![Python Version](https://img.shields.io/pypi/pyversions/crossmark-jotform-api.svg)](https://pypi.org/project/crossmark-jotform-api/)
[![License](https://img.shields.io/pypi/l/crossmark-jotform-api.svg)](https://pypi.org/project/crossmark-jotform-api/)
[![CI/CD Pipeline](https://github.com/mirkan1/crossmark-jotform-api/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/mirkan1/crossmark-jotform-api/actions/workflows/ci-cd.yml)
[![Coverage Status](https://coveralls.io/repos/github/mirkan1/crossmark-jotform-api/badge.svg?branch=master)](https://coveralls.io/github/mirkan1/crossmark-jotform-api?branch=master)
[![Tests](https://github.com/mirkan1/crossmark-jotform-api/actions/workflows/test-coverage.yml/badge.svg)](https://github.com/mirkan1/crossmark-jotform-api/actions/workflows/test-coverage.yml)

## 📊 Code Coverage

This project maintains comprehensive test coverage to ensure code quality and reliability.

- **Current Coverage**: ~51% and growing
- **Testing Framework**: pytest with coverage.py
- **Coverage Reports**: HTML, XML, and Terminal formats
- **CI Integration**: Automated coverage reporting via GitHub Actions

### Running Tests Locally

```bash
# Install development dependencies
pip install -r dev_requirements.txt
pip install -e .

# Run tests with coverage
./run_coverage.sh

# Or manually:
pytest --cov=src/crossmark_jotform_api --cov-report=term-missing --cov-report=html --cov-report=xml --cov-branch

# View HTML coverage report
open htmlcov/index.html


# Example command to run a specific unit test:
/home/raq/crossmark-jotform-api && python3 -m unittest tests.test_jotform_unit.TestJotFormUnit.test_create_and_delete_submission -v
```

### Coverage Integration

We use the officially recommended approach for Python coverage reporting:

- **Local Development**: `coverage.py` with HTML reports
- **CI/CD**: GitHub Actions with Coveralls integration
- **Format**: Cobertura XML for maximum compatibility

The project follows Coveralls' recommended setup for Python projects using:

- GitHub Actions for CI
- `coverage.py` to generate Cobertura XML reports  
- Official Coveralls GitHub Action for uploads

## 🚀 CI/CD Pipeline

This project includes a comprehensive CI/CD pipeline that ensures code quality and reliability:

### Automated Testing

- **Multi-Python Version Testing**: Tests run on Python 3.8, 3.9, 3.10, 3.11, and 3.12
- **Pull Request Validation**: All PRs are automatically tested before merging
- **Coverage Threshold**: Minimum 50% test coverage required for CI to pass
- **Quality Gates**: Tests must pass before deployment to PyPI

### Coverage Reporting

- **Dual Coverage Uploads**: Reports sent to both Coveralls and Codecov
- **Branch Coverage**: Comprehensive branch coverage tracking
- **HTML Reports**: Detailed coverage reports available as CI artifacts
- **Coverage Badges**: Real-time coverage status in README

### Deployment

- **Automated PyPI Publishing**: Packages are automatically published to PyPI on master branch pushes
- **Quality Assurance**: Only code that passes all tests and coverage thresholds gets deployed
- **Trusted Publishing**: Uses PyPI's trusted publishing for secure deployments

### Workflow Files

- `.github/workflows/ci-cd.yml` - Main CI/CD pipeline with testing and publishing
- `.github/workflows/test-coverage.yml` - Dedicated coverage reporting and artifact generation

## Examples

```python
from jotform_api import JotformAPI

# Initialize the API with your API key
api = JotformAPI('YOUR_API_KEY')

# Get user details
user = api.get_user()
print(user)

# List all forms
forms = api.get_forms()
for form in forms:
  print(form['title'])

# Get submissions for a specific form
form_id = '1234567890'
submissions = api.get_form_submissions(form_id)
for submission in submissions:
  print(submission)
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

&copy; 2025 [Mirkan](https://github.com/mirkan1)
