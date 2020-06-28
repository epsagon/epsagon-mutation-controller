FROM python:3.7

# set labels for metadata
LABEL maintainer="Epsagon<dev@epsagon.com>" \
  name="auto-inst-mutation-controller" \
  description="A Kubernetes mutating webhook server for auto instrumentation" \
  summary="A Kubernetes mutating webhook server for auto instrumentation"

# set environment variables
ENV USER_UID=1001 \
  USER_NAME=auto-inst-mutation-controller


RUN mkdir /cmd
COPY cmd/requirements.txt /cmd/requirements.txt
RUN pip install -r /cmd/requirements.txt

# install auto-inst-mutation-controller binary
# COPY build/_output/bin/auto-inst-mutation-controller ${EPSAGON_MUTATION_CONTROLLER}
COPY cmd/main.py /cmd/main.py

# # copy licenses
# RUN mkdir /licenses
# COPY LICENSE /licenses

# set entrypoint
ENTRYPOINT ["python", "cmd/main.py"]

# switch to non-root user
USER ${USER_UID}
