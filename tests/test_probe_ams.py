import unittest
from unittest.mock import patch
from unittest.mock import Mock


from argo_ams_library import AmsConnectionException, AmsException, AmsMessage
from argo_probe_ams.NagiosResponse import NagiosResponse
from argo_probe_ams.ams_check import run


def mock_pull_sub_func(*args, **kwargs):
    return [('projects/mock_PROJECT/subscriptions/mock_sensor_sub:0', AmsMessage)]

def mock_pass_func(*args, **kwargs):
    pass


def mock_func_ams_message(*args, **kwargs):
    return AmsMessage(data="mock_data", attributes="mock_attributes")


class ArgoProbeAmsTests(unittest.TestCase):
    def setUp(self):
        arguments = {
            "host": "mock_host",
            "token": "1234",
            "project": "mock_PROJECT",
            "topic": "mock_topic",
            "timeout": 3,
            "subscription": "mock_sensor_sub"
        }
        self.arguments = Mock(**arguments)

    def test_connectionerror_on_hastopic(self):
        run(self.arguments)


if __name__ == '__main__':
    unittest.main()
