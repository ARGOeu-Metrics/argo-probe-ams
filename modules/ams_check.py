#!/usr/bin/env python3

import random
from argparse import ArgumentParser

from argo_ams_library import ArgoMessagingService, AmsException
from argo_probe_ams.NagiosResponse import NagiosResponse
from argo_probe_ams.utils.file_utils import cleanup_from_temp_file, delete_host_from_tmp, write_to_temp_file
from argo_probe_ams.utils.messaging_service import create_msg, publish_msgs


def utils(arguments):
    nagios = NagiosResponse("All messages received correctly.")

    try:
        ams = ArgoMessagingService(
            endpoint=arguments.host, token=arguments.token, project=arguments.project)

        is_deleted = cleanup_from_temp_file(ams, arguments.host)

        if ams.has_topic(arguments.topic, timeout=arguments.timeout):
            ams.delete_topic(arguments.topic, timeout=arguments.timeout)

        if ams.has_sub(arguments.subscription, timeout=arguments.timeout):
            ams.delete_sub(arguments.subscription, timeout=arguments.timeout)

        ams.create_topic(arguments.topic, timeout=arguments.timeout)
        ams.create_sub(arguments.subscription, arguments.topic,
                       timeout=arguments.timeout)
                   
        msg_array, msg_orig = create_msg(nagios, arguments)
        rcv_msg = publish_msgs(ams, arguments, msg_array, nagios)

        ams.delete_topic(arguments.topic, timeout=arguments.timeout)
        ams.delete_sub(arguments.subscription, timeout=arguments.timeout)

        if msg_orig != rcv_msg:
            nagios.writeCriticalMessage("Messages received incorrectly.")
            nagios.setCode(nagios.CRITICAL)

        delete_host_from_tmp(is_deleted, arguments)

        print(nagios.getMsg())
        raise SystemExit(nagios.getCode())

    except (AmsException) as e:
        write_to_temp_file(arguments.host, arguments.topic, arguments.subscription)
        nagios.setCode(nagios.CRITICAL)
        nagios.writeCriticalMessage(str(e))
        print(nagios.getMsg())
        raise SystemExit(nagios.getCode())
    

def main():
    TIMEOUT = 180
    random_bits = ("%032x" % random.getrandbits(128))[:16]

    parser = ArgumentParser(description="Nagios sensor for AMS")
    parser.add_argument('-H', dest='host', type=str,
                        default='messaging-devel.argo.grnet.gr', help='FQDN of AMS Service')
    parser.add_argument('--token', type=str, required=True, help='Given token')
    parser.add_argument('--project', type=str, required=True,
                        help='Project registered in AMS Service')
    parser.add_argument('--topic', type=str,
                        default=f"test_topic_{random_bits}", help='Given topic')
    parser.add_argument('--subscription', type=str,
                        default=f"test_subsc_{random_bits}", help='Subscription name')
    parser.add_argument('-t', dest='timeout', type=int,
                        default=TIMEOUT, help='Timeout')
    cmd_options = parser.parse_args()

    utils(arguments=cmd_options)


if __name__ == "__main__":
    main()
