#!/usr/bin/env python3

import random
import string
import hashlib
import json

from argparse import ArgumentParser
from argo_ams_library import ArgoMessagingService, AmsMessage, AmsException, AmsMessageException
from argo_probe_ams.statefile import StateFile
from argo_probe_ams.NagiosResponse import NagiosResponse


MSG_NUM = 100
MSG_SIZE = 500
STATE_FILE = "/var/spool/argo/argo-probe-ams/resources.json"


def gen_rand_str(length=16):
    characters = string.ascii_lowercase + string.digits
    random_string = ''.join(random.choices(characters, k=length))
    return random_string


def create_resources(ams, arguments):
    topic = arguments.topic
    subscription = arguments.subscription
    timeout = arguments.timeout

    ams.create_topic(topic, timeout=timeout)
    ams.create_sub(subscription, topic, timeout=timeout)


def delete_resources(ams, arguments):
    if isinstance(arguments, dict):
        ams.delete_topic(arguments['topic'], timeout=arguments['timeout'])
        ams.delete_sub(arguments['subscription'], timeout=arguments['timeout'])
    else:
        ams.delete_topic(arguments.topic, timeout=arguments.timeout)
        ams.delete_sub(arguments.subscription, timeout=arguments.timeout)


def pub_pull(ams, arguments, msg_array):
    ams.publish(arguments.topic, msg_array, timeout=arguments.timeout)

    ackids = []
    rcv_msg_hashs = set()

    for id, msg in ams.pull_sub(arguments.subscription, MSG_NUM, True, timeout=arguments.timeout):
        attr = msg.get_attr()

        hash_obj = hashlib.md5((msg.get_data().decode(
            'utf-8') + list(attr.keys())[0] + list(attr.values())[0]).encode()
        )
        rcv_msg_hashs.add(hash_obj.hexdigest())
        ackids.append(id)

    if ackids:
        ams.ack_sub(arguments.subscription, ackids,
                    timeout=arguments.timeout)

    return rcv_msg_hashs


def construct_msgs(MSG_NUM, MSG_SIZE):
    ams_msg = AmsMessage()
    msg_array = list()
    msg_hash = set()

    for i in range(1, MSG_NUM):
        msg_txt = ''.join(random.choice(
            string.ascii_letters + string.digits) for i in range(MSG_SIZE))
        attr_name = ''.join(random.choice(
            string.ascii_letters + string.digits) for i in range(5))
        attr_value = ''.join(random.choice(
            string.ascii_letters + string.digits) for i in range(8))

        msg_array.append(
            ams_msg(data=msg_txt, attributes={attr_name: attr_value})
        )

        hash_obj = hashlib.md5((msg_txt + attr_name + attr_value).encode())
        msg_hash.add(hash_obj.hexdigest())

    return msg_array, msg_hash


def run(arguments):
    nagios = NagiosResponse("All messages received correctly.")
    ams = ArgoMessagingService(endpoint=arguments.host, token=arguments.token,
                               project=arguments.project)
    state_file = StateFile(STATE_FILE, arguments.host)

    exists, resources = state_file.check(arguments.host)
    if exists:
        resources['timeout'] = arguments.timeout
        delete_resources(ams, resources)

    try:
        create_resources(ams, arguments)

    except AmsException as exc:
        try:
            state_file.record(arguments)

        except OSError as exc:
            nagios.writeUnknownMessage(f"{STATE_FILE} - {repr(exc)}")
            nagios.setCode(nagios.UNKNOWN)
            print(nagios.getMsg())
            raise SystemExit(nagios.getCode())

        else:
            nagios.writeCriticalMessage(exc.msg)
            nagios.setCode(nagios.CRITICAL)
            print(nagios.getMsg())
            raise SystemExit(nagios.getCode())

    try:
        msg_array, msg_hashs = construct_msgs(MSG_NUM, MSG_SIZE)

    except (AmsMessageException, TypeError, AttributeError):
        nagios.setCode(nagios.CRITICAL)
        print(nagios.getMsg())
        raise SystemExit(nagios.getCode())

    try:
        rcv_msg_hashs = pub_pull(ams, arguments, msg_array)
        delete_resources(ams, arguments)

    except AmsException as e:
        try:
            state_file.record(arguments)

        except OSError as exc:
            nagios.writeUnknownMessage(f"{STATE_FILE} - {repr(exc)}")
            nagios.setCode(nagios.UNKNOWN)
            print(nagios.getMsg())
            raise SystemExit(nagios.getCode())

        else:
            nagios.writeCriticalMessage(e.msg)
            nagios.setCode(nagios.CRITICAL)
            print(nagios.getMsg())
            raise SystemExit(nagios.getCode())

    if msg_hashs != rcv_msg_hashs:
        nagios.writeCriticalMessage("Messages received incorrectly.")
        nagios.setCode(nagios.CRITICAL)

    print(nagios.getMsg())
    raise SystemExit(nagios.getCode())


def main():
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
                        default=180, help='Timeout')
    cmd_options = parser.parse_args()

    run(arguments=cmd_options)


if __name__ == "__main__":
    main()
