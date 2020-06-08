FROM alpine:latest

# set labels for metadata
LABEL maintainer="Epsagon<dev@epsagon.com>" \
  name="auto-inst-mutation-controller" \
  description="A Kubernetes mutating webhook server for auto instrumentation" \
  summary="A Kubernetes mutating webhook server for auto instrumentation"

# set environment variables
ENV EPSAGON_MUTATION_CONTROLLER=/usr/local/bin/auto-inst-mutation-controller \
  USER_UID=1001 \
  USER_NAME=auto-inst-mutation-controller

# install auto-inst-mutation-controller binary
COPY build/_output/bin/auto-inst-mutation-controller ${EPSAGON_MUTATION_CONTROLLER}

# # copy licenses
# RUN mkdir /licenses
# COPY LICENSE /licenses

# set entrypoint
ENTRYPOINT ["/usr/local/bin/auto-inst-mutation-controller"]

# switch to non-root user
USER ${USER_UID}
