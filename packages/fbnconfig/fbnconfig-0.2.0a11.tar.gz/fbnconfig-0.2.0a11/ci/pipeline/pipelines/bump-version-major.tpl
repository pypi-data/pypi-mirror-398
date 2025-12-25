merge:
  - template: resources/fbnconfig-semver.tpl

jobs:
  - name: bump-version-major
    plan:
      - put: fbnconfig-version
        params:
          bump: major
