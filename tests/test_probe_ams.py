import unittest
import os
import hashlib

from unittest.mock import patch
from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import MagicMock

from argo_ams_library import (
    AmsConnectionException,
    AmsException,
    AmsMessageException,
    ArgoMessagingService,
)
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
    @patch.object(ArgoMessagingService, 'create_topic')
    def test_connectionerror_on_createtopic(self, m_createtopic, m_statefile):
        instance = m_statefile.return_value
        instance.record = MagicMock()
        instance.check.return_value = (False, None)
        m_createtopic.side_effect = [AmsConnectionException("mocked connection error", "mock_create_topic")]

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
    @patch('argo_probe_ams.check.AmsClient')
    @patch('argo_probe_ams.amsclient.ArgoMessagingService')
    def test_resource_cleanup(self, m_ams, m_amsclient):
        import json
        instance = m_amsclient.return_value
        instance.create.side_effect = [AmsConnectionException("mocked connection error", "mock_create_topic"), True]
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
        self.assertEqual(instance.delete.mock_calls[0], call(content['mock_host']))
        self.assertEqual(instance.delete.mock_calls[1], call(self.arguments3))
        with open(self.mock_state_file, 'r') as fp:
            content = json.loads(fp.read())
            self.assertDictEqual(content, {})

    @patch('argo_probe_ams.check.MSG_NUM', 1)
    @patch('argo_probe_ams.check.StateFile')
    @patch('argo_probe_ams.check.AmsClient')
    @patch('argo_probe_ams.amsclient.ArgoMessagingService')
    def test_resource_failed_cleanup(self, m_ams, m_amsclient, m_statefile):
        import json
        instance = m_amsclient.return_value
        instance2 = m_statefile.return_value
        instance2.check.return_value = [True, {
            'topic': 'mock_topic',
            'subscription': 'mock_subscription'
        }]
        instance.delete.side_effect = [AmsConnectionException("mocked connection error", "mock_delete_topic")]
        with self.assertRaises(SystemExit) as exc:
            run(self.arguments)
        self.assertEqual(exc.exception.code, 2)

    # ------------------------------------------------------------------
    # x_sender_id handling in AmsClient.pub_pull
    # ------------------------------------------------------------------

    @staticmethod
    def _make_pulled_msg(data, attributes):
        """Build a Mock that mimics the AmsMessage interface used by pub_pull."""
        msg = Mock()
        msg.get_data.return_value = data.encode() if isinstance(data, str) else data
        # Return the same dict on every call so pub_pull's `pop` mutates it.
        msg.get_attr.return_value = dict(attributes)
        return msg

    @patch('argo_probe_ams.amsclient.ArgoMessagingService')
    def test_pub_pull_strips_x_sender_id_from_hash(self, m_ams):
        """When the server stamps a non-empty `x_sender_id` on every message,
        pub_pull must strip it before hashing so the returned hashes match
        the publisher-side ones (which never include x_sender_id)."""
        ams_instance = m_ams.return_value
        pulled = [
            ("ackid-1", self._make_pulled_msg(
                "payload-1", {"attrA": "valA", "x_sender_id": "sender-1"})),
            ("ackid-2", self._make_pulled_msg(
                "payload-2", {"attrB": "valB", "x_sender_id": "sender-2"})),
        ]
        ams_instance.pull_sub.return_value = iter(pulled)

        client = AmsClient(self.arguments, MSG_SIZE=10, MSG_NUM=2)
        hashes = client.pub_pull(self.arguments, msg_array=["m1", "m2"])

        expected = {
            hashlib.md5("payload-1attrAvalA".encode()).hexdigest(),
            hashlib.md5("payload-2attrBvalB".encode()).hexdigest(),
        }
        self.assertEqual(hashes, expected)
        ams_instance.publish.assert_called_once_with(
            'mock_topic', ["m1", "m2"], timeout=3)
        ams_instance.pull_sub.assert_called_once_with(
            'mock_sensor_sub', 2, True, timeout=3)
        ams_instance.ack_sub.assert_called_once_with(
            'mock_sensor_sub', ["ackid-1", "ackid-2"], timeout=3)

    @patch('argo_probe_ams.amsclient.ArgoMessagingService')
    def test_pub_pull_missing_x_sender_id_raises(self, m_ams):
        """A pulled message without `x_sender_id` must raise AmsMessageException."""
        ams_instance = m_ams.return_value
        ams_instance.pull_sub.return_value = iter([
            ("ackid-1", self._make_pulled_msg(
                "payload-1", {"attrA": "valA"})),  # no x_sender_id
        ])

        client = AmsClient(self.arguments, MSG_SIZE=10, MSG_NUM=1)
        with self.assertRaises(AmsMessageException) as ctx:
            client.pub_pull(self.arguments, msg_array=["m1"])

        self.assertIn("x_sender_id", ctx.exception.msg)
        # AmsMessageException is a subclass of AmsException, so the
        # existing error handling path in check.run() catches it.
        self.assertIsInstance(ctx.exception, AmsException)
        ams_instance.ack_sub.assert_not_called()

    @patch('argo_probe_ams.amsclient.ArgoMessagingService')
    def test_pub_pull_empty_x_sender_id_raises(self, m_ams):
        """A pulled message whose `x_sender_id` is an empty string must also fail."""
        ams_instance = m_ams.return_value
        ams_instance.pull_sub.return_value = iter([
            ("ackid-1", self._make_pulled_msg(
                "payload-1", {"attrA": "valA", "x_sender_id": ""})),
        ])

        client = AmsClient(self.arguments, MSG_SIZE=10, MSG_NUM=1)
        with self.assertRaises(AmsMessageException) as ctx:
            client.pub_pull(self.arguments, msg_array=["m1"])

        self.assertIn("x_sender_id", ctx.exception.msg)
        ams_instance.ack_sub.assert_not_called()


if __name__ == '__main__':
    unittest.main()
