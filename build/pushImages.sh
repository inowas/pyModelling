#!/usr/bin/env bash

docker login
docker push inowas/pymodelling:latest
docker push inowas/pymodelling:modflow
docker push inowas/pymodelling:optimization
docker push inowas/pymodelling:simulation
docker push inowas/pymodelling:geoprocessing
