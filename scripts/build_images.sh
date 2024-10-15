#!/bin/bash

echo $0

proj_root_dir=$(dirname $(dirname $0))

proj_root_dir=$(cd $proj_root_dir;pwd)

echo $proj_root_dir

curr_dir=$(pwd)

cd $proj_root_dir


docker build -f ./middleware/Dockerfile.pulsar -t synergy/pulsar:3.3.0 ./middleware/






