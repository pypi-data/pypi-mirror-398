#!/bin/bash -e
pushd pipeline
uav merge --pipeline fbnconfig.pipeline.tpl --directory templates -o .pipeline.yml
popd
# to login run below
#fly -t client-engineering login -n client-engineering -c https://concourse.finbourne.com
fly -t client-engineering set-pipeline --config pipeline/.pipeline.yml --pipeline fbnconfig
