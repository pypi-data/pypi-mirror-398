import socket
from vizlab_data_transfer import vizlab
import pytest
import numpy as np
from pytest_mock import MockerFixture


class TestDataReceiveMethods:

    def test_received_data_format(self, mocker: MockerFixture):
        # Cache current socket state (to be reset later)
        currentIP = vizlab.get_ip()
        currentPort = vizlab.get_port()

        # Init socket state for test
        vizlab._reset_socket_state()
        vizlab.set_ip("127.0.0.1")
        vizlab.set_port(26000)

        # Mock the socket.socket constructor
        mock_socket_instance = mocker.MagicMock()
        mocker.patch("socket.socket", return_value=mock_socket_instance)

        # Set recv return values using mocker side effects
        dataSize = (80).to_bytes(4, byteorder="little")
        numDims = (2).to_bytes(4, byteorder="little")
        numTypes = (1).to_bytes(4, byteorder="little")
        dimsBytes = b"".join([i.to_bytes(4, byteorder="little") for i in [10, 2]])
        typesBytes = b"".join([i.to_bytes(4, byteorder="little") for i in [6]])
        dataBytes = np.random.rand(10, 2).astype(np.float32).tobytes()
        messageSize = (104).to_bytes(4)
        
        mock_socket_instance.recv.side_effect = [
            messageSize,
            dataSize + numDims + numTypes + dimsBytes + typesBytes + dataBytes,
        ]

        # Assertions
        assert vizlab.receive().shape == (10, 2)
        mock_socket_instance.connect.assert_called_with(("127.0.0.1", 26000))

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
