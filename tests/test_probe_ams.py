import unittest
from unittest.mock import patch
from unittest.mock import Mock
from unittest.mock import MagicMock

from argo_ams_library import AmsConnectionException, AmsException, AmsMessage, ArgoMessagingService
from argo_probe_ams.NagiosResponse import NagiosResponse
from argo_probe_ams.ams_check import run


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
        self.patcher1 = patch('argo_probe_ams.ams_check.STATE_FILE', '/tmp/ams-probe-state.json')
        self.mock_state_file = self.patcher1.start()

    def tearDown(self):
        patch.stopall()

    @patch('argo_probe_ams.ams_check.record_resource')
    @patch.object(ArgoMessagingService, 'has_topic')
    def test_connectionerror_on_hastopic(self, m_hastopic, m_recordresource):
        m_hastopic.side_effect = [AmsConnectionException("mocked connection error", "mock_has_topic")]

        with self.assertRaises(SystemExit) as exc:
            run(self.arguments)
        self.assertEqual(exc.exception.code, 2)
        m_recordresource.assert_called_with('mock_host', 'mock_topic', 'mock_sensor_sub')

    @patch('argo_probe_ams.ams_check.MSG_NUM', 1)
    @patch('argo_probe_ams.ams_check.MSG_SIZE', 10)
    @patch('argo_probe_ams.ams_check.record_resource')
    @patch('argo_probe_ams.ams_check.create_resources')
    @patch('argo_probe_ams.ams_check.AmsMessage')
    @patch('argo_probe_ams.ams_check.ArgoMessagingService')
    def test_connectionerror_on_pull(self, m_ams, m_ams_msg, m_create_reso, m_record_reso):
        instance = m_ams.return_value
        instance.pull_sub = MagicMock()
        instance.pull_sub.side_effect = [AmsConnectionException("mocked connection error", "mock_pull_sub")]
        with self.assertRaises(SystemExit) as exc:
            run(self.arguments)
        instance.pull_sub.assert_called_with('mock_sensor_sub', 1, True, timeout=3)
        m_record_reso.assert_called_with('mock_host', 'mock_topic', 'mock_sensor_sub')
        self.assertEqual(exc.exception.code, 2)

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
        with self.assertRaises(SystemExit) as exc:
            run(self.arguments)
        self.assertEqual(exc.exception.code, 0)
        with open(self.mock_state_file, 'r') as fp:
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
