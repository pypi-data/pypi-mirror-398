#!/bin/bash
# Author: Daniel Bosk <dbosk@kth.se>
# License: MIT
# Description: Generates the address ranges for the given lab rooms.
# Usage: ./addresses.sh <lab room> <lab room> ...
# The lab room is the hostname prefix, eg red (for Röd) or toke (for Toker).

LABROOMS_CSV=$(mktemp)
list_lab_computer_hostnames_IPs() {
  local rooms=$*
  local room
  for room in $rooms; do
    for num in $(seq -w 1 99); do
      host $room-$num.eecs.kth.se | grep -v NXDOMAIN | grep -v IPv6 \
        | cut -d " " -f 1,4
      host $room$num.eecs.kth.se | grep -v NXDOMAIN | grep -v IPv6 \
        | cut -d " " -f 1,4
      host $room-$num.ug.kth.se | grep -v NXDOMAIN \
        | cut -d " " -f 1,4
      host $room$num.ug.kth.se | grep -v NXDOMAIN \
        | cut -d " " -f 1,4
    done
  done
}
get_start_end_address() {
  local room=$1
  local addresses=$(grep -i $room $LABROOMS_CSV | cut -d " " -f 2)
  local start=$(echo "$addresses" | head -n 1)
  local end=$(echo "$addresses" | tail -n 1)
  echo $start $end
}

rooms=$*
list_lab_computer_hostnames_IPs $rooms > $LABROOMS_CSV
for room in $rooms; do
  get_start_end_address $room
done
