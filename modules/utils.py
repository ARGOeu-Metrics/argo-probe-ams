import hashlib
import random
import string

from argo_ams_library import AmsMessage


def gen_rand_str(length=16):
    characters = string.ascii_lowercase + string.digits
    random_string = ''.join(random.choices(characters, k=length))
    return random_string


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
