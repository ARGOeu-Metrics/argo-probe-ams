#!/usr/bin/env python3

import random, string, hashlib

from argparse import ArgumentParser
from argo_ams_library import ArgoMessagingService, AmsMessage, AmsException, AmsMessageException
from argo_probe_ams.NagiosResponse import NagiosResponse

MSG_NUM = 100
MSG_SIZE = 500
msg_orig = set()


def utils(arguments):
    
    nagios = NagiosResponse("All messages received correctly.")
    ams = ArgoMessagingService(endpoint=arguments.host, token=arguments.token, project=arguments.project)

    try:
        
        if ams.has_topic(arguments.topic, timeout=arguments.timeout):        
            ams.delete_topic(arguments.topic, timeout=arguments.timeout)
        
        if ams.has_sub(arguments.subscription, timeout=arguments.timeout):
            ams.delete_sub(arguments.subscription, timeout=arguments.timeout)
        
        ams.create_topic(arguments.topic, timeout=arguments.timeout) 
        ams.create_sub(arguments.subscription, arguments.topic, timeout=arguments.timeout) 
        
    
    
    except AmsException as e:
        nagios.writeCriticalMessage(e.msg)
        nagios.setCode(nagios.CRITICAL)
        print(nagios.getMsg()) 
        raise SystemExit(nagios.getCode())
    

    
    ams_msg = AmsMessage() 
    msg_array = []

    
    try:  
        for i in range(1, MSG_NUM):        
            msg_txt = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(MSG_SIZE))
            attr_name = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(4))
            attr_value = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(8))
            msg_array.append(ams_msg(data=msg_txt, attributes={attr_name: attr_value}))
            hash_obj = hashlib.md5((msg_txt + attr_name + attr_value).encode())
            msg_orig.add(hash_obj.hexdigest())

            
        

    except (AmsMessageException, TypeError, AttributeError):
        nagios.setCode(nagios.CRITICAL)
        print(nagios.getMsg())
        raise SystemExit(2)

    
    try:
        msgs = ams.publish(arguments.topic, msg_array, timeout=arguments.timeout)
        
        ackids = []
        rcv_msg = set()
        for id, msg in ams.pull_sub(arguments.subscription, MSG_NUM - 1, True, timeout=arguments.timeout):     
            attr = msg.get_attr()

            hash_obj = hashlib.md5((msg.get_data().decode('utf-8') + list(attr.keys())[0] + list(attr.values())[0]).encode())
            rcv_msg.add(hash_obj.hexdigest())
            ackids.append(id)
        
        if ackids:
            ams.ack_sub(arguments.subscription, ackids, timeout=arguments.timeout)
      
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

    parser = ArgumentParser(description="Nagios sensor for AMS")
    parser.add_argument('-H', dest='host', type=str, default='messaging-devel.argo.grnet.gr', help='FQDN of AMS Service')
    parser.add_argument('--token', type=str, required=True, help='Given token')
    parser.add_argument('--project', type=str, required=True, help='Project registered in AMS Service')
    parser.add_argument('--topic', type=str, default='nagios_sensor_topic', help='Given topic')
    parser.add_argument('--subscription', type=str, default='nagios_sensor_sub', help='Subscription name')
    parser.add_argument('-t', dest='timeout', type=int, default=TIMEOUT, help='Timeout')
    cmd_options = parser.parse_args()

    utils(arguments=cmd_options)



if __name__ == "__main__":
    main()

