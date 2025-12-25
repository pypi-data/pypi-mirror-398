- task: fbnconfig-sonar
  config:
    platform: linux
    image_resource:
      type: docker-image
      source:
        repository: harbor.finbourne.com/build/python-build-3-11
        username: ((harbor.tools_token_username))
        password: ((harbor.tools_token))
    inputs:
      - name: fbnconfig-version
      - name: source-code-fbnconfig
    run:
      path: bash
      dir: source-code-fbnconfig
      args:
        - -ce
        - |
          
          export SONAR_BRANCH=$(cat .git/branch)
          export version=$(cat ../fbnconfig-version/version)
          chmod +x ci/pipeline/scripts/run_sonar.sh
          ci/pipeline/scripts/run_sonar.sh
    params:
      SONAR_TOKEN: ((sonar.token))
      SONAR_PROJECT_NAME: "fbnconfig"
