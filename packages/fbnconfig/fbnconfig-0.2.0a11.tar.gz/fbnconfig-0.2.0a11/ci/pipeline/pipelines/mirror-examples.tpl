merge:
  - template: resources/fbnconfig-semver.tpl
  - template: resources/source-code-fbnconfig.tpl
  - template: resources/slack-alert.tpl

jobs:
  - name: mirror-examples
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
    - task: copy-examples
      config:
        platform: linux
        image_resource:
          type: docker-image
          source:
            repository: harbor.finbourne.com/alpine/git
            username: robot$concourse
            password: ((harbor.alpine_token))
        inputs:
          - name: source-code-fbnconfig
        params:
          GITLAB_SSH_PRIVATE_KEY: ((gitlab.id_rsa))
        run:
          path: sh
          dir: source-code-fbnconfig
          args:
          - -c
          - -e
          - -u
          - -o
          - pipefail
          - |
            echo "Starting Replication"
            export MAIN_BRANCH="master"

            mkdir -p ~/.ssh
            echo "$GITLAB_SSH_PRIVATE_KEY" > id_rsa
            chmod 400 id_rsa
            mv id_rsa ~/.ssh/
            ssh-keyscan gitlab.com >> ~/.ssh/known_hosts

            git clone git@gitlab.com:finbourne/clientengineering/fbnconfig-examples-mirror.git
            cd fbnconfig-examples-mirror
            rm -rf ./*
            cp -rf ../public_examples/* .

            git config user.name "Concourse"
            git config user.email "concourse@finbourne.com"
            git add -A

            if [[ -z "$(git status --porcelain)" ]]; then
                echo "No changes to commit."
                exit 0
            else
                echo "Changes to commit"
                git commit -asm "Publishing examples"
                git push -u origin $MAIN_BRANCH --force;
                exit 0
            fi
