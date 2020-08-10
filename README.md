# Epsagon Mutation Controller
Deployment mutation controller for auto-traced kubernetes containers, ensuring containers remain auto-traced by Epsagon.
Supported kubernetes versions: > 1.15.0.

## build image

```
make image
```

## deploy to cluster
```
source kubernetes/deploy.sh
```


### Used code from
* https://github.com/morvencao/kube-mutating-webhook-tutorial
* https://github.com/alex-leonhardt/k8s-mutate-webhook
