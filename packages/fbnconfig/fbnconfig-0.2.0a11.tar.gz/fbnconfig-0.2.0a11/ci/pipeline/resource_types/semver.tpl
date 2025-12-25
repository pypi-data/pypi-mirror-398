resource_types:
  - name: semver
    type: docker-image
    source:
      repository: harbor.finbourne.com/tools/semver-resource
      username: ((harbor.tools_token_username))
      password: ((harbor.tools_token))
