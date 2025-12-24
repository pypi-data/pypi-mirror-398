import os
import sys
import unittest
from unittest.mock import Mock

from ovos_bus_client.message import Message
from ovos_utils.messagebus import FakeBus

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from ovos_phal_plugin_connectivity_events import ConnectivityEvents, ConnectivityState


class TestPlugin(unittest.TestCase):
    config = {"disable_scheduled_checks": True}
    bus = FakeBus()
    plugin = ConnectivityEvents(bus=bus, config=config)

    def test_plugin(self):
        self.assertEqual(self.plugin.state, ConnectivityState.UNKNOWN)

        on_network_connect = Mock()
        on_internet_connect = Mock()
        on_network_disconnect = Mock()
        on_internet_disconnect = Mock()
        on_notify_no_internet = Mock()
        on_internet_state = Mock()
        on_network_state = Mock()
        self.bus.on("mycroft.network.connected", on_network_connect)
        self.bus.on("mycroft.internet.connected", on_internet_connect)
        self.bus.on("mycroft.network.disconnected", on_network_disconnect)
        self.bus.on("mycroft.internet.disconnected", on_internet_disconnect)
        self.bus.on("enclosure.notify.no_internet", on_notify_no_internet)
        self.bus.on("mycroft.internet.state", on_internet_state)
        self.bus.on("mycroft.network.state", on_network_state)

        def _reset_mocks():
            for m in (on_network_connect, on_internet_connect,
                      on_network_disconnect, on_internet_disconnect,
                      on_notify_no_internet, on_internet_state,
                      on_network_state):
                m.reset_mock()

        # No Connection -> Network
        test_message = Message("test")
        self.plugin.update_state(ConnectivityState.PORTAL, test_message)
        on_network_connect.assert_called_once()
        on_internet_connect.assert_not_called()
        on_network_disconnect.assert_not_called()
        on_internet_disconnect.assert_not_called()
        on_notify_no_internet.assert_not_called()  # Should this emit?
        on_internet_state.assert_called_once()
        self.assertEqual(on_internet_state.call_args[0][0].data['state'],
                         'disconnected')
        on_network_state.assert_called_once()
        self.assertEqual(on_network_state.call_args[0][0].data['state'],
                         'connected')
        self.assertEqual(self.plugin.state, ConnectivityState.PORTAL)

        _reset_mocks()
        # Network -> Internet
        self.plugin.update_state(ConnectivityState.FULL, test_message)
        on_network_connect.assert_not_called()
        on_internet_connect.assert_called_once()
        on_network_disconnect.assert_not_called()
        on_internet_disconnect.assert_not_called()
        on_notify_no_internet.assert_not_called()
        on_internet_state.assert_called_once()
        self.assertEqual(on_internet_state.call_args[0][0].data['state'],
                         'connected')
        on_network_state.assert_called_once()
        self.assertEqual(on_network_state.call_args[0][0].data['state'],
                         'connected')
        self.assertEqual(self.plugin.state, ConnectivityState.FULL)

        _reset_mocks()
        # Internet -> Network
        self.plugin.update_state(ConnectivityState.LIMITED, test_message)
        on_network_connect.assert_not_called()
        on_internet_connect.assert_not_called()
        on_network_disconnect.assert_not_called()
        on_internet_disconnect.assert_called_once()
        on_notify_no_internet.assert_called_once()
        on_internet_state.assert_called_once()
        self.assertEqual(on_internet_state.call_args[0][0].data['state'],
                         'disconnected')
        on_network_state.assert_called_once()
        self.assertEqual(on_network_state.call_args[0][0].data['state'],
                         'connected')
        self.assertEqual(self.plugin.state, ConnectivityState.LIMITED)

        _reset_mocks()
        # Network -> No Network
        self.plugin.update_state(ConnectivityState.NONE, test_message)
        on_network_connect.assert_not_called()
        on_internet_connect.assert_not_called()
        on_network_disconnect.assert_called_once()
        on_internet_disconnect.assert_not_called()
        on_notify_no_internet.assert_called_once()  # Should this be called?
        on_internet_state.assert_called_once()
        self.assertEqual(on_internet_state.call_args[0][0].data['state'],
                         'disconnected')
        on_network_state.assert_called_once()
        self.assertEqual(on_network_state.call_args[0][0].data['state'],
                         'disconnected')
        self.assertEqual(self.plugin.state, ConnectivityState.NONE)

        _reset_mocks()
        # No Network -> Internet
        self.plugin.update_state(ConnectivityState.FULL, test_message)
        on_network_connect.assert_called_once()
        on_internet_connect.assert_called_once()
        on_network_disconnect.assert_not_called()
        on_internet_disconnect.assert_not_called()
        on_notify_no_internet.assert_not_called()
        on_internet_state.assert_called_once()
        self.assertEqual(on_internet_state.call_args[0][0].data['state'],
                         'connected')
        on_network_state.assert_called_once()
        self.assertEqual(on_network_state.call_args[0][0].data['state'],
                         'connected')
        self.assertEqual(self.plugin.state, ConnectivityState.FULL)

        _reset_mocks()
        # Internet -> No Network
        self.plugin.update_state(ConnectivityState.NONE, test_message)
        on_network_connect.assert_not_called()
        on_internet_connect.assert_not_called()
        on_network_disconnect.assert_called_once()
        on_internet_disconnect.assert_called_once()
        on_notify_no_internet.assert_called_once()
        on_internet_state.assert_called_once()
        self.assertEqual(on_internet_state.call_args[0][0].data['state'],
                         'disconnected')
        on_network_state.assert_called_once()
        self.assertEqual(on_network_state.call_args[0][0].data['state'],
                         'disconnected')
        self.assertEqual(self.plugin.state, ConnectivityState.NONE)


if __name__ == "__main__":
    unittest.main()
