import unittest
from unittest.mock import patch
from unittest.mock import Mock


from argo_ams_library import AmsConnectionException, AmsException, AmsMessage, ArgoMessagingService
from argo_probe_ams.NagiosResponse import NagiosResponse
from argo_probe_ams.ams_check import run
from argo_probe_ams.ams_check import record_resource


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

    @patch('argo_probe_ams.ams_check.record_resource')
    @patch.object(ArgoMessagingService, 'has_topic')
    def test_connectionerror_on_hastopic(self, m_hastopic, m_recordresource):
        m_hastopic.side_effect = [AmsConnectionException("mocked connection error", "mock_has_topic")]

        with self.assertRaises(SystemExit) as exc:
            run(self.arguments)
        self.assertEqual(exc.exception.code, 2)
        m_recordresource.assert_called_with('mock_host', 'mock_topic', 'mock_sensor_sub')

    def test_failed_statewrite(self):
        with self.assertRaises(SystemExit) as exc:
            run(self.arguments)
        self.assertEqual(exc.exception.code, 3)


if __name__ == '__main__':
    unittest.main()
