#!/usr/bin/env python

import random, string, hashlib

from argparse import ArgumentParser
from argo_ams_library import ArgoMessagingService, AmsMessage, AmsException
from NagiosResponse import NagiosResponse

def main():
    MSG_NUM = 100
    MSG_SIZE = 500
    TIMEOUT = 180

    parser = ArgumentParser(description="Nagios sensor for AMS")
    parser.add_argument('-H', dest='host', type=str, default='messaging-devel.argo.grnet.gr', help='FQDN of AMS Service')
    parser.add_argument('--token', type=str, required=True, help='Given token')
    parser.add_argument('--project', type=str, required=True, help='Project registered in AMS Service')
    parser.add_argument('--topic', type=str, default='nagios_sensor_topic', help='Given topic')
    parser.add_argument('--subscription', type=str, default='nagios_sensor_sub', help='Subscription name')
    parser.add_argument('-t', dest='timeout', type=int, default=TIMEOUT, help='Timeout')
    cmd_options = parser.parse_args()

    nagios = NagiosResponse("All messages received correctly.")
    ams = ArgoMessagingService(endpoint=cmd_options.host, token=cmd_options.token, project=cmd_options.project)
    try:
        if ams.has_topic(cmd_options.topic, timeout=cmd_options.timeout):
            ams.delete_topic(cmd_options.topic, timeout=cmd_options.timeout)

        if ams.has_sub(cmd_options.subscription, timeout=cmd_options.timeout):
            ams.delete_sub(cmd_options.subscription, timeout=cmd_options.timeout)

        ams.create_topic(cmd_options.topic, timeout=cmd_options.timeout)
        ams.create_sub(cmd_options.subscription, cmd_options.topic, timeout=cmd_options.timeout)

    except AmsException as e:
        nagios.writeCriticalMessage(e.msg)
        nagios.setCode(nagios.CRITICAL)
        print(nagios.getMsg())
        raise SystemExit(nagios.getCode())

    ams_msg = AmsMessage()
    msg_orig = set()
    msg_array = []

    for i in range(1, MSG_NUM):
        msg_txt = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(MSG_SIZE))
        attr_name = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(4))
        attr_value = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(8))
        msg_array.append(ams_msg(data=msg_txt, attributes={attr_name: attr_value}))
        hash_obj = hashlib.md5(msg_txt + attr_name + attr_value)
        msg_orig.add(hash_obj.hexdigest())

    try:
        msgs = ams.publish(cmd_options.topic, msg_array, timeout=cmd_options.timeout)

        ackids = []
        rcv_msg = set()
        for id, msg in ams.pull_sub(cmd_options.subscription, MSG_NUM - 1, True, timeout=cmd_options.timeout):
            attr = msg.get_attr()

            hash_obj = hashlib.md5(msg.get_data() + attr.keys()[0] + attr.values()[0])
            rcv_msg.add(hash_obj.hexdigest())

        if ackids:
            ams.ack_sub(cmd_options.subscription, ackids, timeout=cmd_options.timeout)

        ams.delete_topic(cmd_options.topic, timeout=cmd_options.timeout)
        ams.delete_sub(cmd_options.subscription, timeout=cmd_options.timeout)

    except AmsException as e:
        nagios.writeCriticalMessage(e.msg)
        nagios.setCode(nagios.CRITICAL)
        print(nagios.getMsg())
        raise SystemExit(nagios.getCode())

    if msg_orig != rcv_msg:
        nagios.writeCriticalMessage("Messages received incorrectly.")
        nagios.setCode(nagios.CRITICAL)

    print(nagios.getMsg())
    raise SystemExit(nagios.getCode())


if __name__ == "__main__":
    main()
