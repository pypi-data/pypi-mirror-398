merge:
  - template: resource_types/semver.tpl

resources:
  - name: fbnconfig-version
    type: semver
    icon: exponent
    source:
      driver: git
      branch: master
      uri: git@gitlab.com:finbourne/cicd/versions.git
      file: fbnconfig.version
      initial_version: 0.0.1
      private_key: ((gitlab.id_rsa))
