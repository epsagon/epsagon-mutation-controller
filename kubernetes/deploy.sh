export IMAGE_REPO ?= epsagon
export IMAGE_NAME ?= auto-inst-mutation-controller
kubectl create ns epsagon-mutation
cat webhook_template.yaml | ./webhook-patch-ca-bundle.sh > webhook_deployment.yaml
./webhook-create-signed-cert.sh
kubectl apply -f webhook_deployment.yaml
