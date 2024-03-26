#!/usr/bin/env python3

import random
import string
import hashlib

from argparse import ArgumentParser
from argo_ams_library import ArgoMessagingService, AmsMessage, AmsException, AmsMessageException
from argo_probe_ams.NagiosResponse import NagiosResponse


STATE_FILE = "/var/spool/argo/argo-probe-ams/state.json"


MSG_NUM = 100
MSG_SIZE = 500
msg_orig = set()


def gen_rand_str(length=16):
    characters = string.ascii_lowercase + string.digits
    random_string = ''.join(random.choices(characters, k=length))
    return random_string


def create_resources(ams, arguments):
    topic = arguments.topic
    subscription = arguments.subscription
    timeout = arguments.timeout

    if ams.has_topic(topic, timeout=timeout):
        ams.delete_topic(topic, timeout=timeout)

    if ams.has_sub(subscription, timeout=timeout):
        ams.delete_sub(subscription, timeout=timeout)

    ams.create_topic(topic, timeout=timeout)
    ams.create_sub(subscription, topic, timeout=timeout)


def record_resource(host, topic, subscription):
    res = dict(host=host, topic=topic, subscription=subscription)
    with open(STATE_FILE, 'a') as fp:
        json.dump(res, fp, indent=4)


def run(arguments):
    nagios = NagiosResponse("All messages received correctly.")
    ams = ArgoMessagingService(endpoint=arguments.host, token=arguments.token,
                               project=arguments.project)

    try:
        record_resource(arguments.host, arguments.topic, arguments.subscription)
        create_resources(ams, arguments)

    except AmsException as exc:
        nagios.writeCriticalMessage(exc.msg)
        nagios.setCode(nagios.CRITICAL)
        print(nagios.getMsg())
        raise SystemExit(nagios.getCode())

    except OSError as exc:
        nagios.writeUnknownMessage(f"{STATE_FILE} - {repr(exc)}")
        nagios.setCode(nagios.UNKNOWN)
        print(nagios.getMsg())
        raise SystemExit(nagios.getCode())

    ams_msg = AmsMessage()
    msg_array = []

    try:
        for i in range(1, MSG_NUM):
            msg_txt = ''.join(random.choice(
                string.ascii_letters + string.digits) for i in range(MSG_SIZE))
            attr_name = ''.join(random.choice(
                string.ascii_letters + string.digits) for i in range(4))
            attr_value = ''.join(random.choice(
                string.ascii_letters + string.digits) for i in range(8))
            msg_array.append(
                ams_msg(data=msg_txt, attributes={attr_name: attr_value}))
            hash_obj = hashlib.md5((msg_txt + attr_name + attr_value).encode())
            msg_orig.add(hash_obj.hexdigest())

    except (AmsMessageException, TypeError, AttributeError):
        nagios.setCode(nagios.CRITICAL)
        print(nagios.getMsg())
        raise SystemExit(2)

    try:
        msgs = ams.publish(arguments.topic, msg_array,
                           timeout=arguments.timeout)

        ackids = []
        rcv_msg = set()

        for id, msg in ams.pull_sub(arguments.subscription, MSG_NUM - 1, True, timeout=arguments.timeout):
            attr = msg.get_attr()

            hash_obj = hashlib.md5((msg.get_data().decode(
                'utf-8') + list(attr.keys())[0] + list(attr.values())[0]).encode())
            rcv_msg.add(hash_obj.hexdigest())
            ackids.append(id)

        if ackids:
            ams.ack_sub(arguments.subscription, ackids,
                        timeout=arguments.timeout)

        ams.delete_topic(arguments.topic, timeout=arguments.timeout)
        ams.delete_sub(arguments.subscription, timeout=arguments.timeout)

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


def main():
    TIMEOUT = 180
    rand_str = gen_rand_str()

    parser = ArgumentParser(description="Nagios sensor for AMS")
    parser.add_argument('-H', dest='host', type=str,
                        default='messaging-devel.argo.grnet.gr', help='FQDN of AMS Service')
    parser.add_argument('--token', type=str, required=True, help='Given token')
    parser.add_argument('--project', type=str, required=True,
                        help='Project registered in AMS Service')
    parser.add_argument('--topic', type=str,
                        default=f"amsprobe-topic_{rand_str}",
                        help='Topic name')
    parser.add_argument('--subscription', type=str,
                        default=f"amsprobe-subscription_{rand_str}",
                        help='Subscription name')
    parser.add_argument('-t', dest='timeout', type=int,
                        default=TIMEOUT, help='Timeout')
    cmd_options = parser.parse_args()

    run(arguments=cmd_options)

if __name__ == "__main__":
    main()
