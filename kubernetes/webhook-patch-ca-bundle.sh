#!/bin/bash

ROOT=$(cd $(dirname $0)/../../; pwd)

set -o errexit
set -o nounset
set -o pipefail

export CA_BUNDLE=$(kubectl config view --raw --minify --flatten -o jsonpath='{.clusters[].cluster.certificate-authority-data}')

if [ -z "${CA_BUNDLE}" ] ; then
    export CA_BUNDLE=$(kubectl get secrets -o jsonpath="{.items[?(@.metadata.annotations['kubernetes\.io/service-account\.name']=='default')].data.ca\.crt}")
fi

if command -v envsubst >/dev/null 2>&1; then
    cat webhook_template.yaml | envsubst > webhook_deployment.yaml
else
    cat webhook_template.yaml | sed -e "s|\${CA_BUNDLE}|${CA_BUNDLE}|g" > webhook_deployment_1.yaml
    cat webhook_deployment_1.yaml | sed -e "s|\${IMAGE_REPO}|${IMAGE_REPO}|g" > webhook_deployment_2.yaml
    cat webhook_deployment_2.yaml | sed -e "s|\${IMAGE_NAME}|${IMAGE_NAME}|g" > webhook_deployment_3.yaml
    cat webhook_deployment_3.yaml | sed -e "s|\${EPSAGON_TOKEN}|${EPSAGON_TOKEN}|g" > webhook_deployment.yaml
    rm -f webhook_deployment_*.yaml
fi
