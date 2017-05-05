#!/bin/bash
set -e
IMAGE_NAME="mgw-monitor-redis"
ELASTICA_VERSION="1.0"
sudo docker build --rm . -t "${IMAGE_NAME}":"${ELASTICA_VERSION}"
