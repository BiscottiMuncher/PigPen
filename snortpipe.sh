#!/bin/bash

## Snort Handler
# Takes in arguments that change the snort application, acts as an API for the python script


### Idea
# Ruleset change and edit
# Logging change an edit
# Config change and edit
# Alert type change and edit


## COMPLETED
# Turn Snort On and Off (Yay)

## Fields

SOCKET="/tmp/snortSock.sock"
#configVar=/usr/local/etc/snort/snort.lua
#rulesetVar=/usr/local/etc/rules/local.rules
#alertTypeVar=alert_json
#loggingDirVar=/var/log/snort/

## Base snort argument

#Create Unix listen socket FD
[ -e "$SOCKET" ] && rm -f "$SOCKET"

## Start snort
startSnort(){
        ## DO not  try and run it from a different file
        snort $@ &
        snPid=$!
        echo "!> STARTED SNORT"
}


## GRacefully kill snort when finished
# Can also apparently use pkill
killSnort(){
        ## Changed this from kill to pkill, couldnt easily track the PID across files (I could but im lazy :p )
        echo "!> KILLING SNORT"
        # Gracefully kill snort with pkill, easy win
        pkill -15 snort3
}


## Main Case loop, goed through all the cases depending on pipe entry
echo "Handler listening at $SOCKET"
socat - UNIX-LISTEN:$SOCKET,fork | while read -r cmd; do
        case "$cmd" in
                start*) args="${cmd#start }"; startSnort $args ;;
                kill) killSnort ;;
                quit) break ;;
                *) echo "Unknown Command $cmd" ;;
        esac
done

echo "Out of loop, Deleting Socket"
## Delete Pipe
rm -f "$SOCKET"
echo "Deleted $SOCKET"
exit 0
