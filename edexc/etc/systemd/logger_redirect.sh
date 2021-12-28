#!/bin/bash

# edexc starts edex_container with the systemd init script (PID 1) so only that 
# output is displayed in the docker log.
# this prints logs to the docker logger so it is viewable with processc/tfc output
journalctl -o cat -fu listener_start.service >> /proc/1/fd/1 &
