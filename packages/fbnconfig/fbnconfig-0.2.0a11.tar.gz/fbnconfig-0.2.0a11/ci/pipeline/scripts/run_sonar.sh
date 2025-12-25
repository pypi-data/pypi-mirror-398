#!/usr/bin/env bash
# This script only tests against Sonar
# SONAR_BRANCH - the branch to output to in Sonarqube
# IS_LOCAL - only run in local mode.  No is for pipelines only.
# version (e.g. 0.0.1)
set -e
echo Passed parameters:
echo - IS_LOCAL="${IS_LOCAL}"
echo - SONAR_PROJECT_NAME="${SONAR_PROJECT_NAME}"
echo - SONAR_BRANCH="${SONAR_BRANCH}"
echo - version="${version}"
echo - PWD="$(pwd)"
echo
cd fbnconfig
ln -s /bin/sonar*/bin/sonar-scanner /bin/sonar-scanner
# Start SONAR
echo "sonar-scanner -Dsonar.login=${SONAR_TOKEN} -Dsonar.projectVersion=${version} -Dsonar.branch.name=${SONAR_BRANCH} -Dsonar.projectKey=${SONAR_PROJECT_NAME} -Dsonar.python.coverage.reportPaths=coverage.xml"
sonar-scanner -Dsonar.login="${SONAR_TOKEN}" -X \
  -Dsonar.projectVersion="${version}" \
  -Dsonar.branch.name="${SONAR_BRANCH}" \
  -Dsonar.projectKey="${SONAR_PROJECT_NAME}" \
  -Dsonar.host.url=https://sonar.finbourne.com \
  -Dsonar.python.coverage.reportPaths=../coverage.xml
