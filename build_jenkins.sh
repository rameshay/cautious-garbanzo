#!/bin/bash
dirs=$(find . -name "mgw*" -type d)
for dir in $dirs; do 
    pushd $dir
    ./build_docker.sh 
    echo "sudo docker tag $dir:1.0 730926784978.dkr.ecr.us-west-2.amazonaws.com/dev/el-$dir:1.0"
    sudo docker tag $dir:1.0 730926784978.dkr.ecr.us-west-2.amazonaws.com/dev/el-$dir:1.0
    echo "sudo docker push 730926784978.dkr.ecr.us-west-2.amazonaws.com/dev/el-$dir:1.0"
    sudo docker push 730926784978.dkr.ecr.us-west-2.amazonaws.com/dev/el-$dir:1.0
    popd
