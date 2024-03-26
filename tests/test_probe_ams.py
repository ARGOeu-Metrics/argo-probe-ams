import unittest
from unittest.mock import patch
from unittest.mock import Mock
from unittest.mock import MagicMock


from argo_ams_library import AmsConnectionException, AmsException, AmsMessage, ArgoMessagingService
from argo_probe_ams.NagiosResponse import NagiosResponse
from argo_probe_ams.ams_check import run
from argo_probe_ams.ams_check import record_resource
from argo_probe_ams.ams_check import create_resources
from argo_probe_ams.ams_check import STATE_FILE


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

    @patch('argo_probe_ams.ams_check.open')
    def test_failed_statewrite(self, m_open):
        m_open.side_effect = PermissionError('mocked perm denied')
        with self.assertRaises(SystemExit) as exc:
            run(self.arguments)
        self.assertEqual(exc.exception.code, 3)

    @patch('argo_probe_ams.ams_check.MSG_NUM', 1)
    @patch('argo_probe_ams.ams_check.ArgoMessagingService')
    @patch('argo_probe_ams.ams_check.AmsMessage')
    def test_success_statewrite(self, m_ams, m_ams_msg):
        import json
        m_ams = MagicMock()
        m_ams_msg = MagicMock()
        with self.assertRaises(SystemExit) as exc:
            run(self.arguments)
        self.assertEqual(exc.exception.code, 0)
        with open(STATE_FILE, 'r') as fp:
            content = json.loads(fp.read())
            self.assertDictEqual(content,
                {
                    'host': 'mock_host',
                    'topic': 'mock_topic',
                    'subscription': 'mock_sensor_sub'
                }
            )


if __name__ == '__main__':
    unittest.main()
