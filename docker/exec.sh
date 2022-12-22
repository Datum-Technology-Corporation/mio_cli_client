exec.sh
#!/bin/sh
docker exec -it \
    -u $(id -u):$(id -g) \
    mio "$@"