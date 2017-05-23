#!/bin/bash
dirs="mgw-monitor mgw-monitor-cfg mgw-monitor-websvr"
for dir in $dirs; do 
    pushd $dir
    echo "$PWD building..."
    ./build_docker_image.sh 
    echo "sudo docker tag $dir:latest 730926784978.dkr.ecr.us-west-2.amazonaws.com/dev/el-$dir:1.0"
    sudo docker tag $dir:latest 730926784978.dkr.ecr.us-west-2.amazonaws.com/dev/el-$dir:1.0
    echo "sudo docker push 730926784978.dkr.ecr.us-west-2.amazonaws.com/dev/el-$dir:1.0"
    sudo docker push 730926784978.dkr.ecr.us-west-2.amazonaws.com/dev/el-$dir:1.0
    popd
done
