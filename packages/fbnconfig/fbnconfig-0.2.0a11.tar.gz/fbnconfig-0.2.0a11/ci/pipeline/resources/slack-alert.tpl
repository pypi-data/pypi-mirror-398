merge:
  - template: resource_types/slack-notification.tpl

resources:
  - name: slack-alert
    type: slack-notification
    icon: slack
    source:
      url: ((slack.url))
