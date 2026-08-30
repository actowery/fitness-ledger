# Security policy

Please report suspected vulnerabilities through GitHub's private vulnerability reporting feature once it is enabled in the repository settings. Until then, contact the repository maintainer privately; do not open a public issue.

Do not include personal health data, access tokens, or private source exports in reports.

## Maintainer controls

The default branch is intended to accept changes only through pull requests that pass CI. GitHub repository rules must require review from code owners, including for changes to workflow, release, and plugin-installation files. The maintainer is the current code owner for all paths.

GitHub Actions should run with the minimum permissions declared in each workflow. Third-party actions are pinned to commit SHAs and updated only through reviewed pull requests.

Before release, maintainers must run the test suite, review dependencies, and confirm that fixtures contain only synthetic data.
