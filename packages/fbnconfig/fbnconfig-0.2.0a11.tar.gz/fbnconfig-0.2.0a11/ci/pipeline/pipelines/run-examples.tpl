merge:
  - template: resources/fbnconfig-semver.tpl
  - template: resources/source-code-fbnconfig.tpl
  - template: resources/slack-alert.tpl

jobs:
  - name: run-examples
    {{include "on_failure_slack_alert_with_authors.tpl" | indentSub 4}}
    serial: true
    plan:
    - get: source-code-fbnconfig
      trigger: true
      passed:
        - build
    - get: fbnconfig-version
      passed:
        - build
    - task: integration-test
      timeout: 40m
      config:
        platform: linux
        image_resource:
          type: docker-image
          source:
            repository: harbor.finbourne.com/tools/fbn-task-runner
            tag: v1latest
            username: ((harbor.tools_token_username))
            password: ((harbor.tools_token))
        inputs:
          - name: source-code-fbnconfig
          - name: fbnconfig-version
        params:
           LUSID_ENV: "https://fbn-qa.lusid.com"
           FBN_ACCESS_TOKEN: ((config-dsl.pat))
           HARBOR_USERNAME: ((harbor.tools_token_username))
           HARBOR_PASSWORD: ((harbor.tools_token))
        run:
          path: fbn-task-runner
          args:
            - --working-dir=source-code-fbnconfig
            - --team=client-engineering
            - --pipeline=fbnconfig
            - --job=run-examples
            - --script=./source-code-fbnconfig/ci/pipeline/scripts/run-examples.sh
            - --image=harbor.finbourne.com/build/python-build-3-11-dind:0.0.2
            - --cpu=1000m
            - --memory=2Gi
            - --timeout-seconds=2400
            - --privileged
