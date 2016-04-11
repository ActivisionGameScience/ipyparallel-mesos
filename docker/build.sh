#! /bin/bash -xe

DOCKER_REGISTRY=jdennison

docker build -t ${DOCKER_REGISTRY}/ipyparallel-marathon-controller:${DOCKER_TAG} -f ./controller/Dockerfile.controller .
docker build -t ${DOCKER_REGISTRY}/ipyparallel-marathon-engine:${DOCKER_TAG} -f ./engine/Dockerfile.engine .

if [ "$DOCKER_TAG" == "dev" ]; then
    echo "dev build. not shipping"
else
    docker push ${DOCKER_REGISTRY}/ipyparallel-marathon-controller:${DOCKER_TAG}
    docker push ${DOCKER_REGISTRY}/ipyparallel-marathon-engine:${DOCKER_TAG}
fi
