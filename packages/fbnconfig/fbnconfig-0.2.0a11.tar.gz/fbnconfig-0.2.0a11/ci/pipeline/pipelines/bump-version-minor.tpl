merge:
  - template: resources/fbnconfig-semver.tpl

jobs:
  - name: bump-version-minor
    plan:
      - put: fbnconfig-version
        params:
          bump: minor
