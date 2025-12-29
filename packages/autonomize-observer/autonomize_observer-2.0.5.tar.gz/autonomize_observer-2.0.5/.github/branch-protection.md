# Branch Protection Rules

To ensure code quality and prevent merging without passing tests, configure the following branch protection rules in GitHub:

## For `main` branch:

1. Go to Settings → Branches → Add rule
2. Branch name pattern: `main`
3. Enable these protections:

### ✅ Required Status Checks
- [x] Require status checks to pass before merging
- [x] Require branches to be up to date before merging
- Required status checks:
  - `Test Results`
  - `test (3.12)`
  - `Coverage Report`

### ✅ Pull Request Requirements
- [x] Require a pull request before merging
- [x] Require approvals: 1
- [x] Dismiss stale pull request approvals when new commits are pushed
- [x] Require review from CODEOWNERS

### ✅ Additional Settings
- [x] Require conversation resolution before merging
- [x] Require signed commits (optional)
- [x] Include administrators
- [x] Restrict who can push to matching branches (optional)

## For `develop` branch (if used):

Apply similar rules but potentially with:
- Fewer required approvals (0-1)
- Less strict status checks

## GitHub Settings for Release

1. Go to Settings → Actions → General
2. Under "Workflow permissions":
   - [x] Read and write permissions
   - [x] Allow GitHub Actions to create and approve pull requests

3. Go to Settings → Environments
4. Create `pypi` environment:
   - Required reviewers: 1-2 (optional)
   - Environment secrets:
     - `PYPI_API_TOKEN`: Your PyPI API token

## Required Secrets

Add these secrets in Settings → Secrets → Actions:
- `PYPI_API_TOKEN`: PyPI API token for publishing packages
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions

## Release Process

1. Create a new release draft on GitHub
2. Set tag to `v0.0.10` format
3. Write release notes
4. Publish release (not just save draft)
5. GitHub Actions will automatically:
   - Validate version matches pyproject.toml
   - Run full test suite
   - Build package
   - Publish to PyPI
   - Attach build artifacts to release