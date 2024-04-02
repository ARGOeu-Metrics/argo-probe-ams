import hashlib

from argo_ams_library import ArgoMessagingService


class AmsClient(object):
    def __init__(self, arguments, MSG_SIZE, MSG_NUM):
        self.MSG_SIZE = MSG_SIZE
        self.MSG_NUM = MSG_NUM
        self.ams = ArgoMessagingService(endpoint=arguments.host,
                                        token=arguments.token,
                                        project=arguments.project)

    def create(self, arguments):
        topic = arguments.topic
        subscription = arguments.subscription
        timeout = arguments.timeout

        self.ams.create_topic(topic, timeout=timeout)
        self.ams.create_sub(subscription, topic, timeout=timeout)

    def delete(self, arguments):
        if isinstance(arguments, dict):
            if self.ams.has_topic(arguments['topic'], timeout=arguments['timeout']):
                self.ams.delete_topic(arguments['topic'], timeout=arguments['timeout'])
            if self.ams.has_sub(arguments['subscription'], timeout=arguments['timeout']):
                self.ams.delete_sub(arguments['subscription'], timeout=arguments['timeout'])
        else:
            if self.ams.has_topic(arguments.topic, timeout=arguments.timeout):
                self.ams.delete_topic(arguments.topic, timeout=arguments.timeout)
            if self.ams.has_sub(arguments.subscription, timeout=arguments.timeout):
                self.ams.delete_sub(arguments.subscription, timeout=arguments.timeout)

    def pub_pull(self, arguments, msg_array):
        self.ams.publish(arguments.topic, msg_array, timeout=arguments.timeout)

        ackids = []
        rcv_msg_hashs = set()

        for id, msg in self.ams.pull_sub(arguments.subscription, self.MSG_NUM,
                                         True, timeout=arguments.timeout):
            attr = msg.get_attr()

            hash_obj = hashlib.md5((msg.get_data().decode(
                'utf-8') + list(attr.keys())[0] + list(attr.values())[0]).encode()
            )
            rcv_msg_hashs.add(hash_obj.hexdigest())
            ackids.append(id)

        if ackids:
            self.ams.ack_sub(arguments.subscription, ackids,
                             timeout=arguments.timeout)

        return rcv_msg_hashs
