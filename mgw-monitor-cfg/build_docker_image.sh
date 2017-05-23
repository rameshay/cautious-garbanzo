#!/bin/bash
set -e
IMAGE_NAME=`basename $PWD`
ELASTICA_VERSION="latest"
sudo docker build --rm . -t "${IMAGE_NAME}":"${ELASTICA_VERSION}"
