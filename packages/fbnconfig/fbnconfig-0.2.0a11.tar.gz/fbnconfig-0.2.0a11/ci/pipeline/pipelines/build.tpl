merge:
  - template: resources/fbnconfig-semver.tpl
  - template: resources/source-code-fbnconfig.tpl
  - template: resources/slack-alert.tpl

jobs:
  - name: build
    {{include "on_failure_slack_alert_with_authors.tpl" | indentSub 4}}
    serial: true
    plan:
    - get: source-code-fbnconfig
      trigger: true
    - get: fbnconfig-version
    - task: unit-test
      timeout: 5m
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
        outputs:
          - name: source-code-fbnconfig
        run:
          dir: source-code-fbnconfig
          path: bash
          args:
          - -ce
          - -u
          - -o
          - pipefail
          - |
            
            uv sync --frozen
            uv run pytest --cov-branch --cov=fbnconfig --cov-report=xml --tb=no --cov-report=term tests/unit -n auto
    {{ include "sonar.tpl" | indentSub 4 }}
    {{ include "dependency-scan.tpl" | indentSub 4 }}
    - put: fbnconfig-version
      params:
          bump: patch
    - put: source-code-fbnconfig
      params:
        repository: source-code-fbnconfig
        tag: fbnconfig-version/version
        only_tag: true
        tag_prefix: v
