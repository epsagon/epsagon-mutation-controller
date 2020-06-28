# Image URL to use all building/pushing image targets;
# Use your own container registry and image name for dev/test by overridding the
# IMAGE_REPO, IMAGE_NAME and IMAGE_TAG environment variable.
IMAGE_REPO ?= epsagon
IMAGE_NAME ?= auto-inst-mutation-controller

PWD := $(shell pwd)
BASE_DIR := $(shell basename $(PWD))

IMAGE_TAG ?= $(shell date +v%Y%m%d)-$(shell git describe --match=$(git rev-parse --short=8 HEAD) --tags --always --dirty)


LOCAL_OS := $(shell uname)
ifeq ($(LOCAL_OS),Linux)
    TARGET_OS ?= linux
    XARGS_FLAGS="-r"
else ifeq ($(LOCAL_OS),Darwin)
    TARGET_OS ?= darwin
    XARGS_FLAGS=
else
    $(error "This system's OS $(LOCAL_OS) isn't recognized/supported")
endif

all: test build image

test:
	@echo "Running the tests for $(IMAGE_NAME)..."
	@pytest cmd/

image: build-image push-image

build-image: build
	@echo "Building the container image: $(IMAGE_REPO)/$(IMAGE_NAME):$(IMAGE_TAG)..."
	@podman build -t $(IMAGE_REPO)/$(IMAGE_NAME):$(IMAGE_TAG) -f build/Dockerfile .

push-image: build-image
	@echo "Pushing the container image for $(IMAGE_REPO)/$(IMAGE_NAME):$(IMAGE_TAG) and $(IMAGE_REPO)/$(IMAGE_NAME):latest..."
	@podman tag $(IMAGE_REPO)/$(IMAGE_NAME):$(IMAGE_TAG) $(IMAGE_REPO)/$(IMAGE_NAME):latest
	@podman push $(IMAGE_REPO)/$(IMAGE_NAME):$(IMAGE_TAG)
	@podman push $(IMAGE_REPO)/$(IMAGE_NAME):latest

clean:
	@rm -rf build/_output

.PHONY: all test build image clean

