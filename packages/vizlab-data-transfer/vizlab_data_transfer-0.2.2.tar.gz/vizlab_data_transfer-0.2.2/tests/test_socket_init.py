import socket
from vizlab_data_transfer import vizlab
import pytest
import numpy as np
from pytest_mock import MockerFixture


class TestSocketInitMethods:

    def test_no_socket_state_set(self, mocker: MockerFixture):
        # Cache current socket state (to be reset later)
        currentIP = vizlab.get_ip()
        currentPort = vizlab.get_port()

        # Init socket state for test
        vizlab._reset_socket_state()

        # Mock the socket.socket constructor
        mock_socket_instance = mocker.MagicMock()
        mocker.patch("socket.socket", return_value=mock_socket_instance)

        # Create test data to send
        data = np.random.rand(10, 2)

        # Assertions
        with pytest.raises(
            ValueError,
            match="The current IP address None and port number None is not valid. Please use the 'set_ip' and 'set_port' methods to fix this!",
        ):
            vizlab.send([data])

        # Bring socket state back to what it was pre-test
        vizlab._reset_socket_state()
        try:
            vizlab.set_ip(currentIP)
        except:
            print("did not reset ip as it was invalid")
        else:
            print("reset ip")
        try:
            vizlab.set_port(currentPort)
        except:
            print("did not reset port as it was invalid")
        else:
            print("reset port")

    def test_ip_set_but_not_port(self, mocker: MockerFixture):
        # Cache current socket state (to be reset later)
        currentIP = vizlab.get_ip()
        currentPort = vizlab.get_port()

        # Init socket state for test
        vizlab._reset_socket_state()
        vizlab.set_ip("127.0.0.1")

        # Mock the socket.socket constructor
        mock_socket_instance = mocker.MagicMock()
        mocker.patch("socket.socket", return_value=mock_socket_instance)

        # Create test data to send
        data = np.random.rand(10, 2)

        # Assertions
        with pytest.raises(
            ValueError,
            match="The current port number None is not valid. Please use the 'set_port' method to fix this!",
        ):
            result = vizlab.send([data])

        # Bring socket state back to what it was pre-test
        vizlab._reset_socket_state()
        try:
            vizlab.set_ip(currentIP)
        except:
            print("did not reset ip as it was invalid")
        else:
            print("reset ip")
        try:
            vizlab.set_port(currentPort)
        except:
            print("did not reset port as it was invalid")
        else:
            print("reset port")

    def test_port_set_but_not_ip(self, mocker: MockerFixture):
        # Cache current socket state (to be reset later)
        currentIP = vizlab.get_ip()
        currentPort = vizlab.get_port()

        # Init socket state for test
        vizlab._reset_socket_state()
        vizlab.set_port(26000)

        # Mock the socket.socket constructor
        mock_socket_instance = mocker.MagicMock()
        mocker.patch("socket.socket", return_value=mock_socket_instance)

        # Create test data to send
        data = np.random.rand(10, 2)

        # Assertions
        with pytest.raises(
            ValueError,
            match="The current IP address None is not valid. Please use the 'set_ip' method to fix this!",
        ):
            vizlab.send([data])

        # Bring socket state back to what it was pre-test
        vizlab._reset_socket_state()
        try:
            vizlab.set_ip(currentIP)
        except:
            print("did not reset ip as it was invalid")
        else:
            print("reset ip")
        try:
            vizlab.set_port(currentPort)
        except:
            print("did not reset port as it was invalid")
        else:
            print("reset port")

    def test_ip_valid(self, mocker: MockerFixture):
        # Cache current socket state (to be reset later)
        currentIP = vizlab.get_ip()
        currentPort = vizlab.get_port()

        # Init socket state for test
        vizlab._reset_socket_state()

        # Mock the socket.socket constructor
        mock_socket_instance = mocker.MagicMock()
        mocker.patch("socket.socket", return_value=mock_socket_instance)

        # Assertions
        with pytest.raises(ValueError, match="The given IP address is not valid."):
            vizlab.set_ip(-1)

        with pytest.raises(ValueError, match="The given IP address is not valid."):
            vizlab.set_ip("0.0.0.0.0")

        assert vizlab.set_ip("127.0.0.1") == True

        # Bring socket state back to what it was pre-test
        vizlab._reset_socket_state()
        try:
            vizlab.set_ip(currentIP)
        except:
            print("did not reset ip as it was invalid")
        else:
            print("reset ip")
        try:
            vizlab.set_port(currentPort)
        except:
            print("did not reset port as it was invalid")
        else:
            print("reset port")

    def test_port_valid(self, mocker: MockerFixture):
        # Cache current socket state (to be reset later)
        currentIP = vizlab.get_ip()
        currentPort = vizlab.get_port()

        # Init socket state for test
        vizlab._reset_socket_state()

        # Mock the socket.socket constructor
        mock_socket_instance = mocker.MagicMock()
        mocker.patch("socket.socket", return_value=mock_socket_instance)

        # Assertions
        with pytest.raises(ValueError, match="The given port number is not valid."):
            vizlab.set_port(-1)

        with pytest.raises(ValueError, match="The given port number is not valid."):
            vizlab.set_port(2010240124)

        with pytest.raises(ValueError, match="The given port number is not valid."):
            vizlab.set_port("not a number")

        assert vizlab.set_port(1100) == True

        vizlab._reset_socket_state()

        # Bring socket state back to what it was pre-test
        try:
            vizlab.set_ip(currentIP)
        except:
            print("did not reset ip as it was invalid")
        else:
            print("reset ip")
        try:
            vizlab.set_port(currentPort)
        except:
            print("did not reset port as it was invalid")
        else:
            print("reset port")
