#!/bin/bash 

# Query marathon find host of ipython paralell controller
CONTROLLER_HOST=`curl $MARATHON_MASTER/v2/apps/$CONTROLLER_MARATHON_ID | jq -r '.app.tasks | .[0].host'`
echo $CONTROLLER_HOST
curl http://${CONTROLLER_HOST}:${CONTROLLER_CONFIG_PORT:-1235}/ipcontroller-engine.json --create-dirs -o /opt/profile_mesos/security/ipcontroller-engine.json
cat /opt/profile_mesos/security/ipcontroller-engine.json
ipengine --profile=mesos --url=tcp://$HOST:$PORT
