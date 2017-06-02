#!/bin/bash

sleep 10
# Start the first process
echo ">> Start inowas_flopy_calculation_server..."
./inowas_flopy_calculation_server $1 $2 $3 $4 $5 $6
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start inowas_flopy_calculation_server: $status"
  exit $status
fi

# Start the second process
./inowas_flopy_readdata_rpc_server $1 $2 $3 $4 $5 $6
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start inowas_flopy_readdata_rpc_server: $status"
  exit $status
fi

# Naive check runs checks once a minute to see if either of the processes exited.
# This illustrates part of the heavy lifting you need to do if you want to run
# more than one service in a container. The container will exit with an error
# if it detects that either of the processes has exited.
# Otherwise it will loop forever, waking up every 60 seconds

while /bin/true; do
  PROCESS_1_STATUS=$(ps aux |grep -q inowas_flopy_calculation_server |grep -v grep)
  PROCESS_2_STATUS=$(ps aux |grep -q inowas_flopy_readdata_rpc_server | grep -v grep)
  # If the greps above find anything, they will exit with 0 status
  # If they are not both 0, then something is wrong
  if [ $PROCESS_1_STATUS -ne 0 -o $PROCESS_2_STATUS -ne 0 ]; then
    echo "One of the processes has already exited."
    exit -1
  fi
  sleep 60
done
