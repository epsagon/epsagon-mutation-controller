if [ -z $IMAGE_REPO ] ; then
    export IMAGE_REPO=epsagon
fi
if [ -z $IMAGE_NAME ] ; then
    export IMAGE_NAME=auto-inst-mutation-controller
fi

usage() {
    cat <<EOF
Deploy Epsagon Mutation Controller

This deploys 
EOF
    exit 1
}

function deploy {
    KUBECTL=$1
    EPSAGON_TOKEN=$2
    ${KUBECTL} create ns epsagon-mutation
    ./webhook-patch-ca-bundle.sh
    ./webhook-create-signed-cert.sh
    ${KUBECTL} apply -f webhook_deployment.yaml
}

function main {
    KUBECTL="kubectl"
    while [[ $# -gt 0 ]]; do
        case ${1} in
            --context)
                KUBECTL="${KUBECTL} --context ${2}"
                shift
                ;;
            --kubeconfig)
                KUBECTL="${KUBECTL} --kubeconfig ${2}"
                shift
                ;;
            --token)
                EPSAGON_TOKEN=${2}
                shift
                ;;
            *)
                usage
                return 1
                ;;
        esac
        shift
    done
    deploy $KUBECTL $EPSAGON_TOKEN
}

main
