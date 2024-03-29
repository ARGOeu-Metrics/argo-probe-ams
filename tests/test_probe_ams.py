import unittest
import os

from unittest.mock import patch
from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import MagicMock

from argo_ams_library import AmsConnectionException, AmsException, AmsMessage, ArgoMessagingService
from argo_probe_ams.NagiosResponse import NagiosResponse
from argo_probe_ams.ams_check import run
from argo_probe_ams.ams_check import record_resource
from argo_probe_ams.ams_check import delete_resources


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
        arguments2 = {
            "host": "mock_host2",
            "token": "5678",
            "project": "mock_PROJECT2",
            "topic": "mock_topic2",
            "timeout": 3,
            "subscription": "mock_sensor_sub2"
        }
        self.arguments2 = Mock(**arguments2)
        arguments3 = {
            "host": "mock_host",
            "token": "5678",
            "project": "mock_PROJECT3",
            "topic": "mock_topic3",
            "timeout": 3,
            "subscription": "mock_sensor_sub3"
        }
        self.arguments3 = Mock(**arguments3)
        self.patcher1 = patch('argo_probe_ams.ams_check.STATE_FILE', '/tmp/ams-probe-resources.json')
        self.mock_state_file = self.patcher1.start()

    def tearDown(self):
        if os.path.exists(self.mock_state_file):
            os.unlink(self.mock_state_file)
        patch.stopall()

    @patch('argo_probe_ams.ams_check.record_resource')
    @patch.object(ArgoMessagingService, 'has_topic')
    def test_connectionerror_on_hastopic(self, m_hastopic, m_recordresource):
        m_hastopic.side_effect = [AmsConnectionException("mocked connection error", "mock_has_topic")]

        with self.assertRaises(SystemExit) as exc:
            run(self.arguments)
        self.assertEqual(exc.exception.code, 2)
        m_recordresource.assert_called_with(self.arguments)

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
        m_record_reso.assert_called_with(self.arguments)
        self.assertEqual(exc.exception.code, 2)

    @patch('argo_probe_ams.ams_check.open')
    def test_failed_statewrite(self, m_open):
        m_open.side_effect = PermissionError('mocked perm denied')
        with self.assertRaises(SystemExit) as exc:
            run(self.arguments)
        self.assertEqual(exc.exception.code, 3)

    def test_record_resource_multi(self):
        import json
        record_resource(self.arguments)
        with open(self.mock_state_file, 'r') as fp:
            content = json.loads(fp.read())
            self.assertDictEqual(
                content,
                {
                    'mock_host': {
                        'topic': 'mock_topic',
                        'subscription': 'mock_sensor_sub'
                    }
                }
            )
        record_resource(self.arguments2)
        with open(self.mock_state_file, 'r') as fp:
            content = json.loads(fp.read())
            self.assertDictEqual(
                content,
                {
                    'mock_host': {
                        'topic': 'mock_topic',
                        'subscription': 'mock_sensor_sub'
                    },
                    'mock_host2': {
                        'topic': 'mock_topic2',
                        'subscription': 'mock_sensor_sub2'
                    }
                }
            )

    @patch('argo_probe_ams.ams_check.MSG_NUM', 1)
    @patch('argo_probe_ams.ams_check.AmsMessage')
    @patch('argo_probe_ams.ams_check.ArgoMessagingService')
    def test_success_resource_record(self, m_ams, m_ams_msg):
        import json
        instance = m_ams.return_value
        instance.create_topic.side_effect = [AmsConnectionException("mocked connection error", "mock_create_topic")]
        with self.assertRaises(SystemExit) as exc:
            run(self.arguments)
        self.assertEqual(exc.exception.code, 2)
        with open(self.mock_state_file, 'r') as fp:
            content = json.loads(fp.read())
            self.assertDictEqual(content,
                {
                    'mock_host': {
                        'topic': 'mock_topic',
                        'subscription': 'mock_sensor_sub'
                    }
                }
            )

    @patch('argo_probe_ams.ams_check.MSG_NUM', 1)
    @patch('argo_probe_ams.ams_check.delete_resources')
    @patch('argo_probe_ams.ams_check.create_resources')
    @patch('argo_probe_ams.ams_check.AmsMessage')
    @patch('argo_probe_ams.ams_check.ArgoMessagingService')
    def test_resource_cleanup(self, m_ams, m_ams_msg, m_create_reso, m_delete_reso):
        import json
        instance = m_ams.return_value
        m_create_reso.side_effect = [AmsConnectionException("mocked connection error", "mock_create_topic"), True]
        with self.assertRaises(SystemExit) as exc:
            run(self.arguments)
        self.assertEqual(exc.exception.code, 2)
        with open(self.mock_state_file, 'r') as fp:
            content = json.loads(fp.read())
            self.assertDictEqual(content,
                {
                    'mock_host': {
                        'topic': 'mock_topic',
                        'subscription': 'mock_sensor_sub'
                    }
                }
            )
        with self.assertRaises(SystemExit) as exc:
            run(self.arguments3)
        content['mock_host']['timeout'] = 3
        self.assertEqual(m_delete_reso.mock_calls[0], call(instance, content['mock_host']))
        self.assertEqual(m_delete_reso.mock_calls[1], call(instance, self.arguments3))


if __name__ == '__main__':
    unittest.main()
