#!/bin/bash

# List of docker image names.
docker_image_names=(
    "python:3.10"
    "python:3.11"
    "python:3.12"
    "python:3.13"
    "python:3.14"
)

list_of_docer_images=$(docker image ls --format 'table {{.Repository}}:{{.Tag}}')

# Pull all docker images if not exists.
for image_name in "${docker_image_names[@]}"; do

    # Check the existance of the target docker image.
    is_img=$(docker image ls --format 'table {{.Repository}}:{{.Tag}}' | grep ${image_name})

    # Pull docker image if not exists.
    if [ -z "${is_img}" ]; then
        docker pull ${image_name}
    fi

done

# Run tests on each docker image.
for image_name in "${docker_image_names[@]}"; do

    # This dicretory will be connected to /.local on the docker container.
    path_dot_local="/tmp/yadopt_dot_local"

    # Make the dot_local directory.
    mkdir ${path_dot_local}

    # Base docker command.
    docker_cmd="docker run --rm -it -v `pwd`:/work -v ${path_dot_local}:/.local -w /work -u `id -u`:`id -g`"

    # Run the test inside a docker container.
    ${docker_cmd} ${image_name} bash -c "python3 -m pip install -e . && python3 tests/run_tests.py"

    # Remove the dot_local directory.
    rm -rf ${path_dot_local}

done

# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
