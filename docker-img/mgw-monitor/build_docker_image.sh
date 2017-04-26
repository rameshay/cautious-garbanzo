#!/bin/bash
set -e
#source ../../../../../packaging/pkgCommon.sh
IMAGE_NAME="el-mgw-monitor"
ELASTICA_VERSION="2.83.0rc"
docker build . -t "${IMAGE_NAME}":"${ELASTICA_VERSION}"
