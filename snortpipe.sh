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
configVar=/usr/local/etc/snort/snort.lua
rulesetVar=/usr/local/etc/rules/local.rules
alertTypeVar=alert_json
loggingDirVar=/var/log/snort/

## Base snort argument

#Create Unix listen socket FD
[ -e "$SOCKET" ] && rm -f "$SOCKET"

## Start snort
startSnort(){
        #snort -c /usr/local/etc/snort/snort.lua -R /usr/local/etc/rules/local.rules -i eth0 -A alert_json -l /var/log/snort/
        snort -c "$configVar" -R "$rulesetVar" -i eth0 -A "$alertTypeVar" -l "$loggingDirVar" &
        snPid=$!
        echo "!> STARTED"
}


## GRacefully kill snort when finished
# Can also apparently use pkill
killSnort(){
        echo "!> KILLING"
        if [ -n "$snPid" ]; then
                kill -15 "$snPid" && echo "Killed Snort at $snPid"
        else
                echo "Snot PID Not Set, Unable to kill"
        fi
}


## Main Case loop, goed through all the cases depending on pipe entry
echo "Handler listening at $SOCKET"
socat - UNIX-LISTEN:$SOCKET,fork | while read -r cmd; do
        case "$cmd" in
                start) startSnort ;;
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