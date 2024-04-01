#!/usr/bin/env python3

import json

from argparse import ArgumentParser

from argo_ams_library import AmsException, AmsMessageException
from argo_probe_ams.NagiosResponse import NagiosResponse
from argo_probe_ams.amsclient import AmsClient
from argo_probe_ams.statefile import StateFile
from argo_probe_ams.utils import construct_msgs
from argo_probe_ams.utils import gen_rand_str

MSG_NUM = 100
MSG_SIZE = 500
STATE_FILE = "/var/spool/argo/argo-probe-ams/resources.json"


def run(arguments):
    nagios = NagiosResponse("All messages received correctly.")
    state_file = StateFile(STATE_FILE, arguments.host)
    ams_client = AmsClient(arguments, MSG_SIZE, MSG_NUM)

    exists, resources = state_file.check(arguments.host)

    if exists:
        resources['timeout'] = arguments.timeout
        ams_client.delete(resources)
        state_file.delete(arguments.host)

    try:
        ams_client.create(arguments)

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
        rcv_msg_hashs = ams_client.pub_pull(arguments, msg_array)
        ams_client.delete(arguments)

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
