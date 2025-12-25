- task: code-dependency-scan-with-wiz
  config:
    platform: linux
    image_resource:
      type: docker-image
      source:
        repository: harbor.finbourne.com/build/wiz-cli
        tag: latest
        username: robot$concourse
        password: ((harbor.build_token))
    inputs:
      - name: source-code-fbnconfig
      - name: fbnconfig-version
    run:
      path: sh
      args:
        - -cel
        - |  
          export OVERRIDE_BUILDSYSTEM=gitlab
          export OVERRIDE_REPOSITORY_SOURCE=gitlab
          export sourcecode=.  
          export WIZ_CI_COLLECT_PARAMS=true
          export WIZ_CI_BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)
          export WIZ_CI_REPO=$(git config --get remote.origin.url)
          export WIZ_CI_COMMIT_HASH=$(git rev-parse HEAD)
          export WIZ_CI_USERNAME=$(git log -1 --pretty=format:'%an')
          
          echo "Wiki-Page: https://wiki.finbourne.com/en/security/howto/trivy-vulnerability-resolution-guide"
          echo "Slack-Channel: #vulnerability_remediation"
          
          #aggregate all the dependencies into one folder(removing duplicates)
          /app/dep-scanner.sh

          echo -------------- Starting Wiz Scan -------------------
          /app/wizcli auth
          /app/wizcli dir scan --path=. 

      dir: source-code-fbnconfig
    params:
      SONAR_TOKEN: ((sonar.token))
      WIZ_CLIENT_SECRET: ((wiz-cli.clientSecret))
