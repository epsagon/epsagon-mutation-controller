export IMAGE_REPO ?= epsagon
export IMAGE_NAME ?= auto-inst-mutation-controller

export KUBECTL="kubectl"

usage() {
    cat <<EOF
Deploy Epsagon Mutation Controller

This deploys 
EOF
    exit 1
}

while [[ $# -gt 0 ]]; do
    case ${1} in
        --context)
            export KUBECTL="${KUBECTL} --context ${2}"
            shift
            ;;
        --kubeconfig)
            export KUBECTL="${KUBECTL} --kubeconfig ${2}"
            shift
            ;;
        *)
            usage
            ;;
    esac
    shift
done


${KUBECTL} create ns epsagon-mutation
cat webhook_template.yaml | ./webhook-patch-ca-bundle.sh > webhook_deployment.yaml
./webhook-create-signed-cert.sh
${KUBECTL} apply -f webhook_deployment.yaml
