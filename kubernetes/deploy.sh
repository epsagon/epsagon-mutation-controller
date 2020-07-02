if [ -z $IMAGE_REPO ] ; then
    export IMAGE_REPO=epsagon
fi
if [ -z $IMAGE_NAME ] ; then
    export IMAGE_NAME=auto-inst-mutation-controller
fi

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
        --token)
            export EPSAGON_TOKEN=${2}
            shift
            ;;
        *)
            usage
            ;;
    esac
    shift
done


${KUBECTL} create ns epsagon-mutation
./webhook-patch-ca-bundle.sh
./webhook-create-signed-cert.sh
${KUBECTL} apply -f webhook_deployment.yaml
