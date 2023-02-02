from types import SimpleNamespace
import unittest
from unittest.mock import patch


from argo_ams_library import AmsConnectionException, AmsException, AmsMessage
from argo_probe_ams.NagiosResponse import NagiosResponse
from argo_probe_ams.ams_check import utils


def mock_pull_sub_func(*args, **kwargs):
    return [('projects/mock_PROJECT/subscriptions/mock_sensor_sub:0', AmsMessage)]

def mock_pass_func(*args, **kwargs):
    pass


def mock_func_ams_message(*args, **kwargs):
    return AmsMessage(data="mock_data", attributes="mock_attributes")

class ArgoProbeAmsTests(unittest.TestCase):
    def setUp(self) -> None:
        arguments = {"host": "mock_host", "token": "1234", "project": "mock_PROJECT",
                     "topic": "mock_topic", "timeout": 3, "subscription": "mock_sensor_sub"}
        self.arguments = SimpleNamespace(**arguments)

    @patch("argo_probe_ams.ams_check.hashlib")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.create_sub")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.create_topic")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.delete_sub")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.delete_topic")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.ack_sub")
    @patch("argo_probe_ams.ams_check.AmsMessage.get_data")
    @patch("argo_probe_ams.ams_check.AmsMessage.get_attr")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.pull_sub")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.publish")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.has_sub")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.has_topic")
    def test_all_passed(self, mock_has_topic, mock_has_sub, mock_publish,
                        mock_pull_sub, mock_get_attr, mock_get_data,
                        mock_ack_sub, mock_delete_topic, mock_delete_sub,
                        mock_create_topic, mock_create_sub, mock_hashlib):
        mock_has_topic.return_value = False
        mock_has_sub.return_value = False
        mock_publish.return_value = {'messageIds': ['0']}
        mock_pull_sub.side_effect = mock_pull_sub_func
        mock_get_attr.return_value = {'mock_key': 'mock_value'}
        mock_get_data.return_value = b'mock_bytes'
        mock_ack_sub.return_value = True
        mock_delete_topic.side_effect = mock_pass_func
        mock_delete_sub.side_effect = mock_pass_func
        mock_hashlib.return_value = "mock_rand"

        with self.assertRaises(SystemExit) as e:
            utils(self.arguments)

        mock_create_topic.assert_called_once_with(
            self.arguments.topic, timeout=self.arguments.timeout)
        mock_create_sub.assert_called_once_with(
            self.arguments.subscription, self.arguments.topic, timeout=self.arguments.timeout)

        self.assertEqual(e.exception.code, 0)

    @patch("argo_probe_ams.ams_check.ArgoMessagingService.has_topic")
    def test_connectionerror_on_hastopic(self, mock_has_topic):
        mock_has_topic.side_effect = AmsConnectionException(
            "failed connection", "http_mock_get")

        with self.assertRaises(SystemExit) as e:
            utils(self.arguments)

        mock_has_topic.assert_called_once()
        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_ams.ams_check.ArgoMessagingService.delete_sub")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.delete_topic")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.create_sub")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.create_topic")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.ack_sub")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.publish")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.has_sub")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.has_topic")
    def test_connectionerror_on_amspublish(self, mock_has_topic, mock_has_sub,
                                           mock_publish, mock_ack_sub,
                                           mock_create_topic,
                                           mock_create_sub,
                                           mock_delete_topic,
                                           mock_delete_sub):
        mock_has_topic.return_value = False
        mock_has_sub.return_value = False
        mock_publish.return_value = False

        with self.assertRaises(SystemExit) as e:
            utils(self.arguments)

        mock_create_topic.assert_called_once_with(
            self.arguments.topic, timeout=self.arguments.timeout)
        mock_create_sub.assert_called_once_with(
            self.arguments.subscription, self.arguments.topic, timeout=self.arguments.timeout)

        self.assertFalse(mock_ack_sub.called)
        self.assertFalse(mock_delete_topic.called)
        self.assertFalse(mock_delete_sub.called)

        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_ams.ams_check.ArgoMessagingService.create_sub")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.create_topic")
    @patch("argo_probe_ams.ams_check.AmsMessage")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.has_sub")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.has_topic")
    def test_connectionerror_on_amsmessage(self, mock_has_topic, mock_has_sub, mock_ams_msg,
                                           mock_create_topic,
                                           mock_create_sub):

        mock_has_topic.return_value = False
        mock_has_sub.return_value = False
        mock_ams_msg.return_value = "mock_ams_msg"

        with self.assertRaises(SystemExit) as e:
            utils(self.arguments)

        mock_create_topic.assert_called_once_with(
            self.arguments.topic, timeout=self.arguments.timeout)
        mock_create_sub.assert_called_once_with(
            self.arguments.subscription, self.arguments.topic, timeout=self.arguments.timeout)

        self.assertEqual(e.exception.code, 2)

    @patch("argo_probe_ams.ams_check.msg_orig")
    @patch("argo_probe_ams.ams_check.random.choice")
    @patch("argo_probe_ams.ams_check.MSG_NUM", 2)
    @patch("argo_probe_ams.ams_check.MSG_SIZE", 3)
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.create_sub")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.create_topic")
    @patch("argo_probe_ams.ams_check.AmsMessage")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.has_sub")
    @patch("argo_probe_ams.ams_check.ArgoMessagingService.has_topic")
    def test_expected_hashlibmd5_and_connectionerror(self, mock_has_topic, mock_has_sub,
                                                     mock_ams_msg, mock_create_topic,
                                                     mock_create_sub,
                                                     mock_random_choice, mock_msg_orig):

        mock_has_topic.return_value = False
        mock_has_sub.return_value = False
        mock_ams_msg.side_effect = mock_func_ams_message
        mock_random_choice.return_value = "mock_rand"

        with self.assertRaises(SystemExit) as e:
            utils(self.arguments)

        mock_create_topic.assert_called_once_with(
            self.arguments.topic, timeout=self.arguments.timeout)
        mock_create_sub.assert_called_once_with(
            self.arguments.subscription, self.arguments.topic, timeout=self.arguments.timeout)

        expected = "e1afc18e33d67cc202bb6056c28013ee"
        mock_msg_orig.add.assert_called_once_with(expected)
        self.assertEqual(e.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
