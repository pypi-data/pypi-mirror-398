merge:
  - template: resource_types/merge-request.tpl

resources:
  - name: merge-request-core
    type: merge-request
    icon: source-pull
    source:
      uri: git@gitlab.com:finbourne/clientengineering/fbnconfig.git
      private_key: ((gitlab.id_rsa))
      private_token: ((gitlab.access_token))

