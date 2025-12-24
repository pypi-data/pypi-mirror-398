import socket
from vizlab_data_transfer import vizlab
import pytest
import numpy as np
from pytest_mock import MockerFixture
import astropy
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image


class TestDataSendMethods:

    def test_compatible_object_types(self, mocker: MockerFixture):
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
        mock_socket_instance.recv.side_effect = [
            (8).to_bytes(4, byteorder="little"),
            b"RESPONSE",
            (8).to_bytes(4, byteorder="little"),
            b"RESPONSE",
            (8).to_bytes(4, byteorder="little"),
            b"RESPONSE",
            (8).to_bytes(4, byteorder="little"),
            b"RESPONSE",
        ]

        # Create test datasets

        # ndarray
        nddata = np.random.rand(10, 2)

        # recarray
        recdata = np.array([(1.0, 2), (3.0, 4)], dtype=[('x', '<f8'), ('y', '<i8')])

        # mpl 2d fig_2d
        fig_2d, ax_2d = plt.subplots()
        x_data = np.linspace(0, 10, 100)
        y_data = np.cos(x_data)
        ax_2d.plot(x_data, y_data, label="Cosine", color="blue", linestyle="--")
        ax_2d.set_xlabel("X")
        ax_2d.set_ylabel("Y")
        ax_2d.set_title("Cosine Plot")
        ax_2d.legend()

        # mpl 3d fig
        fig_3d = plt.figure()
        ax_3d = fig_3d.add_subplot(projection='3d')
        ax_3d.scatter(np.random.rand(100), np.random.rand(100), np.random.rand(100))
        ax_3d.set_xlabel('X Label')
        ax_3d.set_ylabel('Y Label')
        ax_3d.set_zlabel('Z Label')

        # PIL image
        pilimage = Image.fromarray((255*np.random.rand(20, 20)).astype(np.uint8))

        # pandas dataframe
        df = pd.DataFrame(np.array([(1.0, 2), (3.0, 4)], dtype=[('x', '<f8'), ('y', '<i8')]))

        # astropy FITS table
        fitstable = astropy.table.Table([[1, 2, 3], ['A1', 'B1', 'C1']], names=['col_A', 'col_B'])

        # astropy FITS image
        fitsimg = astropy.io.fits.ImageHDU(data=np.random.rand(10, 10))

        # Assertions

        assert vizlab.send(nddata) == "RESPONSE"
        assert vizlab.send([nddata, recdata]) == "RESPONSE"
        assert vizlab.send([pilimage, fig_2d, fig_3d]) == "RESPONSE"
        assert vizlab.send([df, fitstable, fitsimg]) == "RESPONSE"

        mock_socket_instance.connect.assert_called_with(("127.0.0.1", 26000))

        with pytest.raises(
            ValueError,
            match="Provided Python objects must be one of the following types: numpy ndarray or recarray, pandas dataframe, astropy FITS table or image, matplotlib figure, PIL image.",
        ):
            vizlab.send(21912912)

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

    def test_data_names(self, mocker: MockerFixture):
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
        mock_socket_instance.recv.side_effect = [
            (8).to_bytes(4, byteorder="little"),
            b"RESPONSE",
            (8).to_bytes(4, byteorder="little"),
            b"RESPONSE",
            (8).to_bytes(4, byteorder="little"),
            b"RESPONSE",
        ]

        # Create test datasets

        # ndarray
        nddata = np.random.rand(10, 2)

        # recarray
        recdata = np.array([(1.0, 2), (3.0, 4)], dtype=[('x', '<f8'), ('y', '<i8')])

        # PIL image
        pilimage = Image.fromarray((255*np.random.rand(20, 20)).astype(np.uint8))

        # pandas dataframe
        df = pd.DataFrame(np.array([(1.0, 2), (3.0, 4)], dtype=[('x', '<f8'), ('y', '<i8')]))

        # Assertions

        assert vizlab.send(nddata, data_names="test_name") == "RESPONSE"
        assert vizlab.send(nddata, data_names=["test_name"]) == "RESPONSE"
        assert vizlab.send([nddata, recdata], data_names=["name1", "name2"]) == "RESPONSE"

        mock_socket_instance.connect.assert_called_with(("127.0.0.1", 26000))

        with pytest.raises(
            ValueError,
            match="Multiple data names given but only one dataset provided.",
        ):
            vizlab.send(nddata, data_names=["name1", "name2"])

        with pytest.raises(
            ValueError,
            match="Given data names are not in an acceptable format \(must be a single string or list of strings\).",
        ):
            vizlab.send(nddata, data_names=[11, "name2"])

        with pytest.raises(
            ValueError,
            match="Given data names are not in an acceptable format \(must be a single string or list of strings\).",
        ):
            vizlab.send(nddata, data_names=True)

        with pytest.raises(
            ValueError,
            match="Number of data names \(2\) does not match the number of datasets \(3\).",
        ):
            vizlab.send([nddata, pilimage, recdata], data_names=["name1", "name2"])

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


    def test_data_units(self, mocker: MockerFixture):
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
        mock_socket_instance.recv.side_effect = [
            (8).to_bytes(4, byteorder="little"),
            b"RESPONSE",
            (8).to_bytes(4, byteorder="little"),
            b"RESPONSE",
            (8).to_bytes(4, byteorder="little"),
            b"RESPONSE",
        ]

        # Create test datasets

        # ndarray
        nddata = np.random.rand(10, 2)

        # recarray
        recdata = np.array([(1.0, 2), (3.0, 4)], dtype=[('x', '<f8'), ('y', '<i8')])

        print(recdata.dtype.names)

        # Assertions

        assert vizlab.send(nddata, data_units=astropy.units.dimensionless_unscaled) == "RESPONSE"
        # assert vizlab.send(nddata, data_units=[astropy.units.m / astropy.units.s]) == "RESPONSE"
        # assert vizlab.send([nddata, recdata], data_units=[astropy.units.m, "deg     ", astropy.units.s]) == "RESPONSE"

        mock_socket_instance.connect.assert_called_with(("127.0.0.1", 26000))

        with pytest.raises(
            ValueError,
            match="Provided unit must be either an astropy.units instance or a valid FITS-formatted unit string.",
        ):
            vizlab.send(nddata, data_units=["invalid_unit_name"])

        with pytest.raises(
            ValueError,
            match="Number of data units \(2\) does not match the expected number \(3\).",
        ):
            vizlab.send([nddata, recdata], data_units=["m", "s"])

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

