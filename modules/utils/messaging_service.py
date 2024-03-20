import random
import string
import hashlib

from argo_ams_library import AmsMessage, AmsException, AmsMessageException
from argo_probe_ams.utils.file_utils import write_to_temp_file

MSG_NUM = 100
MSG_SIZE = 500


def create_msg(nagios, arguments):
    ams_msg = AmsMessage()
    msg_orig = set()
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

    except (AmsMessageException, TypeError, AttributeError, Exception):
        write_to_temp_file(arguments.host, arguments.topic, arguments.subscription)
        nagios.setCode(nagios.CRITICAL)
        print(nagios.getMsg())
        raise SystemExit(2)

    return msg_array, msg_orig


def publish_msgs(ams, arguments, msg_array, nagios):
    try:
        ams.publish(arguments.topic, msg_array, timeout=arguments.timeout)

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

        return rcv_msg

    except (AmsException, TypeError, AttributeError, Exception) as e:
        write_to_temp_file(arguments.host, arguments.topic, arguments.subscription)
        nagios.writeCriticalMessage(str(e))
        nagios.setCode(nagios.CRITICAL)
        print(nagios.getMsg())
        raise SystemExit(nagios.getCode())