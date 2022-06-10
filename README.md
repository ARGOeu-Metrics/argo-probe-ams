# argo-probe-ams

Probe is inspecting AMS service by trying to publish and consume randomly generated messages. Probe creates a topic and subscription, generates random 100 messages with payload about 500 bytes that tries to publish to service following immediate try of consuming them. If the integrity of messages is preserved on publishing and consuming side, service is working fine and probe will return successful status.

## Synopsis

Sample execution of the probe: 

```
/usr/libexec/argo/probes/ams/ams-probe -H "msg.argo.grnet.gr" -t 60 --token <token> --project <project>
```
