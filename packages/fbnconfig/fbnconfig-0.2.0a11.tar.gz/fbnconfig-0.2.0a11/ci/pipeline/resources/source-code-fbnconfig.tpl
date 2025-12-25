resources:
  - name: source-code-fbnconfig
    type: git
    icon: gitlab
    source:
      uri: git@gitlab.com:finbourne/clientengineering/fbnconfig.git
      branch: master
      private_key: ((gitlab.id_rsa))
      paths:
        - "fbnconfig/*"
        - "public_examples/"
