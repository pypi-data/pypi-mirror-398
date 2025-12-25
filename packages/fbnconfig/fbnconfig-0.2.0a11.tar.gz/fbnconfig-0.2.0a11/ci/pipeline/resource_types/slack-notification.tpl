resource_types:
  - name: slack-notification
    type: docker-image
    source:
      repository: harbor.finbourne.com/tools/slack-notification-resource
      username: ((harbor.tools_token_username))
      password: ((harbor.tools_token))
