merge:
  - template: resources/fbnconfig-semver.tpl
  - template: resources/source-code-fbnconfig.tpl
  - template: resources/slack-alert.tpl

jobs:
  - name: publish-to-pypi
    {{include "on_failure_slack_alert_with_authors.tpl" | indentSub 4}}
    serial: true
    plan:
    - get: source-code-fbnconfig
      passed:
        - run-examples
    - get: fbnconfig-version
      trigger: true
      passed:
        - run-examples
    - task: publish
      timeout: 10m
      config:
        platform: linux
        image_resource:
          type: docker-image
          source:
            repository: harbor.finbourne.com/build/python-build-3-11
            username: ((harbor.tools_token_username))
            password: ((harbor.tools_token))
        inputs:
          - name: source-code-fbnconfig
          - name: fbnconfig-version
        params:
          API_KEY: ((pypi.password))
        run:
          dir: source-code-fbnconfig
          path: bash
          args:
            - -ce
            - |
              
              # set the version
              uv version $(cat ../fbnconfig-version/version)
              uv build
              uv publish --token "${API_KEY}"
              echo "Available at https://pypi.org/project/fbnconfig/"
