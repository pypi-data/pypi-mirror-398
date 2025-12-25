merge:
  - template: resources/merge-request-core.tpl
  - template: resources/fbnconfig-semver.tpl

jobs:
  - name: merge-request
    plan:
    - get: source-code-fbnconfig
      resource: merge-request-core
      version: every
      trigger: true
    - get: fbnconfig-version
      params:
        bump: patch
    - put: merge-request-core
      params:
        repository: source-code-fbnconfig
        status: running
    - task: unit-tests
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
            export PYRIGHT_PYTHON_NODE_VERSION="24.10.0"
            uv sync
            uv run pytest --cov-branch --cov=fbnconfig --cov-report=xml --tb=no --cov-report=term tests/unit -n auto

            uv run pyright
            uv run ruff check

    {{ include "sonar.tpl" | indentSub 4 }}
    on_failure:
        put: merge-request-core
        params:
          repository: source-code-fbnconfig
          status: failed
    on_success:
        put: merge-request-core
        params:
            repository: source-code-fbnconfig
            status: success
