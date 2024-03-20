import json
import os

FILE_PATH = "/var/spool/argo/probes/argo-probe-ams"
FILE_NAME = "ams_cleanup.json"

temp_file_path = os.path.join(FILE_PATH, FILE_NAME) 


def write_to_temp_file(host, topic, subscription):
    if os.path.exists(temp_file_path):
        with open(temp_file_path, 'r') as f:
            data = json.load(f)
    else:
        data = {}

    data[host] = {
        "topic": topic,
        "subscription": subscription
    }

    with open(temp_file_path, 'w') as f:
        json.dump(data, f)
        
        
def delete_host_from_tmp(is_deleted, arguments):
    if len(is_deleted) > 1 and is_deleted[0] == True and is_deleted[1] == True:
        if os.path.exists(temp_file_path):
            with open(temp_file_path, 'r') as f:
                data = json.load(f)
                
            if arguments.host in data:
                del data[arguments.host]

            if not data:
                os.remove(temp_file_path)
                
            else:
                with open(temp_file_path, 'w') as f:
                    json.dump(data, f)


def cleanup_from_temp_file(ams, current_host):       
    is_deleted = list()
    
    if os.path.exists(temp_file_path):
        with open(temp_file_path, 'r') as f:
            data = json.load(f)
               
        for host, info in list(data.items()): 
            if host == current_host:                
                topic = info["topic"]
                subscription = info["subscription"]
                
                if ams.has_topic(topic):
                    ams.delete_topic(topic)
                    is_deleted.append(True)
                    
                if ams.has_sub(subscription):
                    ams.delete_sub(subscription)
                    is_deleted.append(True)

    return is_deleted