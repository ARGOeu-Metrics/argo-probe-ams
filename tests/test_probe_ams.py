import unittest
import os

from unittest.mock import patch
from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import MagicMock

from argo_ams_library import AmsConnectionException, AmsException, AmsMessage, ArgoMessagingService
from argo_probe_ams.NagiosResponse import NagiosResponse
from argo_probe_ams.check import run
from argo_probe_ams.amsclient import AmsClient


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
        self.patcher1 = patch('argo_probe_ams.check.STATE_FILE', '/tmp/ams-probe-resources.json')
        self.mock_state_file = self.patcher1.start()

    def tearDown(self):
        if os.path.exists(self.mock_state_file):
            os.unlink(self.mock_state_file)
        patch.stopall()

    @patch('argo_probe_ams.check.StateFile')
    @patch.object(ArgoMessagingService, 'has_topic')
    def test_connectionerror_on_hastopic(self, m_hastopic, m_statefile):
        instance = m_statefile.return_value
        instance.record = MagicMock()
        instance.check.return_value = (False, None)
        m_hastopic.side_effect = [AmsConnectionException("mocked connection error", "mock_has_topic")]

        with self.assertRaises(SystemExit) as exc:
            run(self.arguments)
        self.assertEqual(exc.exception.code, 2)
        instance.record.assert_called_with(self.arguments)

    @patch('argo_probe_ams.check.MSG_NUM', 1)
    @patch('argo_probe_ams.check.MSG_SIZE', 10)
    @patch('argo_probe_ams.check.StateFile')
    @patch('argo_probe_ams.amsclient.ArgoMessagingService')
    def test_connectionerror_on_pull(self, m_ams, m_statefile):
        instance = m_ams.return_value
        instance2 = m_statefile.return_value
        instance.pull_sub = MagicMock()
        instance.pull_sub.side_effect = [AmsConnectionException("mocked connection error", "mock_pull_sub")]
        instance2.check.return_value = (False, None)
        with self.assertRaises(SystemExit) as exc:
            run(self.arguments)
        instance.pull_sub.assert_called_with('mock_sensor_sub', 1, True, timeout=3)
        instance2.record.assert_called_with(self.arguments)
        self.assertEqual(exc.exception.code, 2)

    @patch('argo_probe_ams.statefile.open')
    def test_failed_statewrite(self, m_open):
        m_open.side_effect = PermissionError('mocked perm denied')
        with self.assertRaises(SystemExit) as exc:
            run(self.arguments)
        self.assertEqual(exc.exception.code, 3)

    @patch('argo_probe_ams.check.MSG_NUM', 1)
    @patch('argo_probe_ams.amsclient.ArgoMessagingService')
    def test_record_resource_multi(self, m_ams):
        import json
        instance = m_ams.return_value
        instance.create_topic.side_effect = [
            AmsConnectionException("mocked connection error", "mock_create_topic"),
            AmsConnectionException("mocked connection error", "mock_create_topic")
        ]
        with self.assertRaises(SystemExit) as exc:
            run(self.arguments)
        self.assertEqual(exc.exception.code, 2)
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
        with self.assertRaises(SystemExit) as exc:
            run(self.arguments2)
        self.assertEqual(exc.exception.code, 2)
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

    @patch('argo_probe_ams.check.MSG_NUM', 1)
    @patch('argo_probe_ams.amsclient.ArgoMessagingService')
    def test_success_resource_record(self, m_ams):
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

    @patch('argo_probe_ams.check.MSG_NUM', 1)
    @patch.object(AmsClient, 'delete')
    @patch.object(AmsClient, 'create')
    @patch('argo_probe_ams.amsclient.ArgoMessagingService')
    def test_resource_cleanup(self, m_ams, m_create, m_delete):
        import json
        m_create.side_effect = [AmsConnectionException("mocked connection error", "mock_create_topic"), True]
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
        self.assertEqual(m_delete.mock_calls[0], call(content['mock_host']))
        self.assertEqual(m_delete.mock_calls[1], call(self.arguments3))


if __name__ == '__main__':
    unittest.main()
