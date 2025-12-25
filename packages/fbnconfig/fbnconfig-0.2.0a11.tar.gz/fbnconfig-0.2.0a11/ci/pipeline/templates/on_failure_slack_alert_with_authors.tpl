on_failure:
  put: slack-alert
  params:
    channel: '#project_fbnconfig'
    icon_emoji: ':boom:'
    text_file: slack/authors
    text: |
      HEY <!channel>! Something went wrong with the fbnconfig build ($BUILD_PIPELINE_NAME/$BUILD_JOB_NAME).
      <https://concourse.finbourne.com/teams/$BUILD_TEAM_NAME/pipelines/$BUILD_PIPELINE_NAME/jobs/$BUILD_JOB_NAME/builds/$BUILD_NAME|Click here for details>
