#!/bin/sh
docker run -d -it --rm --name mio \
    -u $(id -u):$(id -g) \
    -v tools:/tools:ro \
    -v "${PWD}/my_design:/design" \
    -v "${HOME}" \
    mio-client