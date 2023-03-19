[![Maintainability](https://api.codeclimate.com/v1/badges/d2c2952ba3ab41823502/maintainability)](https://codeclimate.com/github/dfar-io/repo-updater/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/d2c2952ba3ab41823502/test_coverage)](https://codeclimate.com/github/dfar-io/repo-updater/test_coverage)

# repo-updater
Updates all my repos with consistent settings

## Settings

1. Turn off all GitHub features except "preserve".
2. Only allow squash comments in merges.
3. Always suggest updating.
4. Allow auto-merge.
5. Automatically delete head branches after merge.

For `main`:

1. Require PR.
2. Require successful status checks.
  a. Require branch up to date (statuc check = build)
3. Do not allow bypass.
