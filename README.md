# argo-probe-ams

Probe is inspecting AMS service by trying to publish and consume randomly generated messages. Probe creates topic and subscription, generates random 100 messages with payload about 500 bytes that tries to publish to service following immediate try of consuming them. If the integrity of messages is preserved on publishing and consuming side, service is working fine and probe will return successful status.

Topic and subscription names are uniquely generated for each run of the probe with common prefix `amsprobe-topic_` and `amsprobe-subscription_` respectively. In case of failures where probe has not managed to conclude the full CRUD round, for example it created topic and published messages but then AMS instance experienced problems and it did not manage to create a subscription and consume published messages, it will record the topic name and try to clean it up on the next run when AMS instance is back. Created resources are recorded in `/var/spool/argo/argo-probe-ams/resources.json`.

For development/testing purposes, topic and subscription names can be fixed by explicitly specifying them as arguments on the probe run.

## Usage

Default arguments:
```
usage: ams-probe [-h] [-H HOST] --token TOKEN --project PROJECT [--topic TOPIC] [--subscription SUBSCRIPTION] [-t TIMEOUT]

Nagios sensor for AMS

optional arguments:
  -h, --help            show this help message and exit
  -H HOST               FQDN of AMS Service
  --token TOKEN         Given token
  --project PROJECT     Project registered in AMS Service
  --topic TOPIC         Topic name
  --subscription SUBSCRIPTION
                        Subscription name
  -t TIMEOUT            Timeout
```

Sample execution of the probe:
```
/usr/libexec/argo/probes/ams/ams-probe -H "msg.argo.grnet.gr" -t 60 --token <token> --project <project>
```
