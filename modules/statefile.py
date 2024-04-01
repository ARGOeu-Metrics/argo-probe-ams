import os
import json


class StateFile(object):
    def __init__(self, state_file, host):
        self.state_file = state_file
        self.host = host

    def record_resource(self, arguments):
        rec = {'topic': arguments.topic, 'subscription': arguments.subscription}
        host = arguments.host
        content = ''

        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as fp:
                content = fp.read()

        if content:
            content = json.loads(content)
            if host in content:
                content[host] = rec
            else:
                content.update({
                    host: rec
                })
            with open(self.state_file, 'w+') as fp:
                json.dump(content, fp, indent=4)
        else:
            with open(self.state_file, 'w+') as fp:
                json.dump({
                    host: rec
                }, fp, indent=4)

    def check_resource_file(self, host):
        content = ''
        res_host = dict()

        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as fp:
                content = fp.read()

        if content:
            content = json.loads(content)
            if host in content:
                res_host = content[host]
                del content[host]
                with open(self.state_file, 'w+') as fp:
                    json.dump(content, fp, indent=4)

                return (True, res_host)

        return (False, None)
