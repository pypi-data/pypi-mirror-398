import socket
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Path3DCollection
from io import BytesIO
import struct
from PIL import Image
import ipaddress
import os
import json
import pandas as pd
from astropy import units
from astropy.units.format import FITS
from astropy.io import fits
from astropy.table import Table

IP = None  # VizLab's local IP address
PORT = None  # VizLab's port number

"""
Send provided data to the VizLab.

Args:
    info (obj or list(obj) or tuple(obj)): Data to send.
"""


def send(info, object_name=None, data_names=None, data_units=None):
    if not _network_info_is_valid():
        return

    # Initialize socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to socket
    s.connect((IP, PORT))

    # Get byte data
    byteData = _serialize_data(info, object_name, data_names, data_units)

    # Send to system via socket
    s.sendall(byteData)

    # Receive response message from system
    header = s.recv(4)
    size = int.from_bytes(header)
    messageBytes = s.recv(size)
    message = messageBytes.decode("utf-8")

    print(message)
    return message


"""
Wait to receive data from the VizLab.

Returns:
    data (ndarray): Deserialized data from the VizLab.
"""


def receive():
    if not _network_info_is_valid():
        return

    # Initialize socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to socket
    s.connect((IP, PORT))

    # Receive data payload size
    sizeBytes = s.recv(4)
    size = int.from_bytes(sizeBytes)

    # Wait to receive all data
    messageBytes = b""
    while len(messageBytes) < size:
        packet = s.recv(size - len(messageBytes))
        if not packet:
            raise ValueError("The connection to the system closed prematurely.")
        messageBytes += packet

    index = 0

    # Parse full data payload
    # header info: DataSize (int), NumDims (int), NumTypes(int)
    dataSize = int.from_bytes(messageBytes[index : index + 4], byteorder="little")
    index += 4

    numDims = int.from_bytes(messageBytes[index : index + 4], byteorder="little")
    index += 4

    numTypes = int.from_bytes(messageBytes[index : index + 4], byteorder="little")
    index += 4

    # Pull out info based on header
    dimsBytes = messageBytes[index : index + (4 * numDims)]
    index += 4 * numDims
    dims = list(struct.unpack("<" + "I" * numDims, dimsBytes))

    typesBytes = messageBytes[index : index + (4 * numTypes)]
    index += 4 * numTypes
    types = list(struct.unpack("<" + "I" * numTypes, typesBytes))

    byteData = messageBytes[index : index + dataSize]
    index += dataSize

    # Deserialize data and return
    data = _deserialize_data(byteData, dims, types)
    return data


"""
Set the module's config-backed IP address, if the provided address is valid.

Args:
    ip (string): Desired IP address
"""


def set_ip(ip):
    global IP
    if IP == None:
        _retrieve_network_info()

    try:
        ipaddress.ip_address(
            ip
        )  # use ipaddress module to check validity of given address

        IP = ip  # update current module state

        # update config state
        _write_to_config("IP", IP)
        print(f"IP successfully set to {IP}.")
        return True

    except:
        raise ValueError("The given IP address is not valid.")


"""
Returns the current IP address stored in a global variable (and locally backed by config.json)

Returns:
    IP (string): Current module IP address
"""


def get_ip():
    global IP
    if IP == None:
        _retrieve_network_info()

    return IP


"""
Set the module's config-backed port number, if the provided port is valid.

Args:
    port (int or valid string format): Desired port
"""


def set_port(port):
    global PORT
    if PORT == None:
        _retrieve_network_info()
    try:
        if int(port) < 0 or int(port) > 65535:
            raise ValueError("The given port number is not valid.")
        else:
            PORT = port

            _write_to_config("PORT", PORT)
            print(f"Port number successfully set to {PORT}.")
            return True
    except:
        raise ValueError("The given port number is not valid.")


"""
Returns the current port number stored in a global variable (and locally backed by config.json)

Returns:
    PORT (int): Current module port
"""


def get_port():
    global PORT
    if PORT == None:
        _retrieve_network_info()

    return PORT


## Managing network state


def _network_info_is_valid():
    # create config file if we don't have one
    if IP == None or PORT == None:
        _retrieve_network_info()

    ip_valid = _ip_is_valid(IP)
    port_valid = _port_is_valid(PORT)
    if not ip_valid and not port_valid:
        raise ValueError(
            f"The current IP address {IP} and port number {PORT} is not valid. Please use the 'set_ip' and 'set_port' methods to fix this!"
        )
    elif not ip_valid:
        raise ValueError(
            f"The current IP address {IP} is not valid. Please use the 'set_ip' method to fix this!"
        )
    elif not port_valid:
        raise ValueError(
            f"The current port number {PORT} is not valid. Please use the 'set_port' method to fix this!"
        )

    return True


def _retrieve_network_info():
    config_path = os.path.dirname(os.path.abspath(__file__)) + "\\config.json"
    # pull data from config file
    if not os.path.isfile(config_path):
        _write_to_config("IP", None)
        _write_to_config("PORT", None)

    with open(config_path, "r") as f:
        data = json.load(f)

        global IP
        IP = data["IP"]

        global PORT
        PORT = data["PORT"]


def _ip_is_valid(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except:
        return False


def _port_is_valid(port):
    try:
        if int(port) < 0 or int(port) > 65535:
            return False
        return True
    except:
        return False


def _reset_socket_state():
    global IP
    IP = None

    global PORT
    PORT = None
    _write_to_config("IP", IP)
    _write_to_config("PORT", PORT)


def _write_to_config(key, value):
    ip = IP if key != "IP" else value
    port = PORT if key != "PORT" else value
    data = {"IP": ip, "PORT": port}
    config_path = os.path.dirname(os.path.abspath(__file__)) + "\\config.json"
    with open(config_path, "w") as json_file:
        json.dump(data, json_file, indent=4)


## Data serialization


def _serialize_data(info, object_name, data_names, data_units):
    _verify_parameters(info, object_name, data_names, data_units)

    if isinstance(info, list) or isinstance(info, tuple):
        byteArray = bytearray()
        unit_index = 0
        for i in range(len(info)):
            finalBlock = True if i == len(info) - 1 else False
            name = "" if data_names == None else data_names[i]
            unit = (
                units.dimensionless_unscaled
                if data_units == None
                else data_units[unit_index : unit_index + _get_num_datasets(info[i])]
            )
            unit_index += _get_num_datasets(info[i])
            byteArray.extend(_serialize_single_data(info[i], name, unit, finalBlock))
        return (
            _serialize_payload_header(
                len(byteArray), ("" if object_name == None else object_name)
            )
            + byteArray
        )
    else:
        name = (
            ""
            if data_names == None
            else (data_names[0] if type(data_names) == list else data_names)
        )
        unit = (
            units.dimensionless_unscaled
            if data_units == None
            else (data_units if type(data_units) == list else [data_units])
        )
        data = _serialize_single_data(info, name, unit, True)
        return (
            _serialize_payload_header(
                len(data), ("" if object_name == None else object_name)
            )
            + data
        )


def _serialize_single_data(info, data_name, data_unit, is_final_block):

    if isinstance(info, np.ndarray) and info.dtype.names is None:
        return _serialize_ndarray_data(info, data_name, data_unit, is_final_block)
    elif isinstance(info, plt.Figure):
        if isinstance(info.get_axes()[0], Axes3D): # see if plot is 3D
            if isinstance(info.get_axes()[0].collections[0], Path3DCollection): # see if plot is 3D scatterplot specifically
                return _serialize_3d_mpl_data(info, data_name, data_unit, is_final_block)
            else:
                return _serialize_2d_mpl_data(info, data_name, data_unit, is_final_block)
        else:
            return _serialize_2d_mpl_data(info, data_name, data_unit, is_final_block)
    elif isinstance(info, Image.Image):
        return _serialize_pil_data(info, data_name, data_unit, is_final_block)
    elif isinstance(info, np.ndarray) and info.dtype.names is not None:
        return _serialize_recarray_data(info, data_unit, is_final_block)
    elif isinstance(info, pd.DataFrame):
        return _serialize_pandas_data(info, data_unit, is_final_block)
    elif isinstance(info, Table):
        return _serialize_astropy_table_data(info, data_unit, is_final_block)
    elif isinstance(info, fits.ImageHDU):
        return _serialize_astropy_image_data(info, data_name, data_unit, is_final_block)
    else:
        raise ValueError(
            "Provided Python objects must be one of the following types: numpy ndarray or recarray, pandas dataframe, astropy FITS table or image, matplotlib figure, PIL image."
        )


def _serialize_payload_header(payload_size, object_name):
    payload_size_header = payload_size.to_bytes(4, byteorder="little")
    object_name_length_header = (len(object_name)).to_bytes(4, byteorder="little")
    object_name_header = object_name.encode("utf-8")

    return payload_size_header + object_name_length_header + object_name_header


def _serialize_data_header(size_in_bytes, dims, dtypes, name, unit, is_final_block):
    # first verify that the data can be accepted by C# 
    # (C# limits on arrays of 2GB in size AND number of elements less that uint32 max value)
    # (but our limits are a little tighter due to needing a Base64 string conversion to pass via RPC call)
    # (the theoretical max is 1.5 GB, but we'll do 1 GB for now until I can test things further!)
    print(size_in_bytes)
    if (size_in_bytes > 1e+9):
        raise ValueError(
        f"One or more datasets exceeds the 1 GB size limit. Please use alternate means to transfer this data, such as Google Drive/Globus!"
        )   

    block_value = 1 if is_final_block else 0
    content_header = (
        size_in_bytes.to_bytes(4, byteorder="little")
        + len(dims).to_bytes(4, byteorder="little")
        + len(dtypes).to_bytes(4, byteorder="little")
        + len(name).to_bytes(4, byteorder="little")
        + len(unit).to_bytes(4, byteorder="little")
        + (block_value).to_bytes(4, byteorder="little")
    )
    dims_header = b"".join([i.to_bytes(4, byteorder="little") for i in dims])
    dtypes_header = b"".join(
        [
            i.to_bytes(1, byteorder="little")
            for i in (
                dtypes if type(dtypes[0]) == int else _get_internal_dtypes(dtypes)
            )
        ]
    )
    dtype_size_header = b"".join(
        [i.to_bytes(4, byteorder="little") for i in _get_dtype_sizes(dtypes)]
    )
    name_header = name.encode("utf-8")
    unit_header = unit.encode("utf-8")

    return (
        content_header
        + dims_header
        + dtypes_header
        + dtype_size_header
        + name_header
        + unit_header
    )


def _serialize_ndarray_data(arr, data_name, data_unit, is_final_block=False):

    # Serialize data
    data = arr.tobytes()

    # Serialize header info
    header = _serialize_data_header(
        arr.nbytes,
        arr.shape,
        [arr.dtype],
        data_name,
        _combine_string_list(_get_units_as_strings(data_unit)),
        is_final_block,
    )

    return header + data


def _serialize_astropy_image_data(img, data_name, data_unit, is_final_block=False):
    return _serialize_ndarray_data(img.data, data_name, data_unit, is_final_block)


def _serialize_recarray_data(arr, data_unit, is_final_block=False):

    # Serialize data
    data = arr.tobytes()

    # Serialize header info
    header = _serialize_data_header(
        arr.nbytes,
        arr.shape + (len(arr.dtype.names),),
        [arr[name].dtype for name in arr.dtype.names],
        _combine_string_list(arr.dtype.names),
        _combine_string_list(_get_units_as_strings(data_unit)),
        is_final_block,
    )

    return header + data


def _serialize_pandas_data(df, data_unit, is_final_block=False):
    # Convert dataframe to np.recarray, then serialize that
    return _serialize_recarray_data(df.to_records(), data_unit, is_final_block)


def _serialize_astropy_table_data(table, data_unit, is_final_block=False):
    # Convert FITS table to np.recarray, then serialize that
    return _serialize_recarray_data(table.as_array(), data_unit, is_final_block)


def _serialize_2d_mpl_data(fig, data_name, data_unit, is_final_block=False):

    # Convert plot to a byte-stored image
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=300)
    buf.seek(0)  # Rewind the buffer to the beginning
    data = bytearray(buf.getvalue())

    # Serialize header info
    header = _serialize_data_header(
        buf.getbuffer().nbytes,
        [int(i) for i in list(fig.get_size_inches())] * 300,
        [13],
        data_name,
        _combine_string_list(_get_units_as_strings(data_unit)),
        is_final_block,
    )

    return header + data

def _serialize_3d_mpl_data(fig, data_name, data_unit, is_final_block=False):

    # Pull out points from plot
    scatter = fig.get_axes()[0].collections[0]
    points = np.array(scatter._offsets3d).T # Need to access private attribute to get at this data!

    # Serialize resulting numpy array
    return _serialize_ndarray_data(points, data_name, data_unit, is_final_block)


def _serialize_pil_data(img, data_name, data_unit, is_final_block=False):

    # Convert PIL Image class to a byte-stored image
    buf = BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()

    # Serialize header info
    header = _serialize_data_header(
        buf.getbuffer().nbytes,
        list(img.size),
        [13],
        data_name,
        _combine_string_list(_get_units_as_strings(data_unit)),
        is_final_block,
    )

    return header + data


def _combine_string_list(lst):
    combined_string = ""
    for i in range(len(lst)):
        combined_string += lst[i]
        combined_string += (
            "\0" if i < len(lst) - 1 else ""
        )  # use null terminator to split in C#
    return combined_string


def _get_internal_dtype(numpy_dtype):
    if numpy_dtype is np.dtype(np.int8):
        return 0
    elif numpy_dtype is np.dtype(np.uint8):
        return 1
    elif numpy_dtype is np.dtype(np.int16):
        return 2
    elif numpy_dtype is np.dtype(np.uint16):
        return 3
    elif numpy_dtype is np.dtype(np.int32):
        return 4
    elif numpy_dtype is np.dtype(np.uint32):
        return 5
    elif numpy_dtype is np.dtype(np.int64):
        return 6
    elif numpy_dtype is np.dtype(np.uint64):
        return 7
    elif numpy_dtype is np.dtype(np.float32):
        return 8
    elif numpy_dtype is np.dtype(np.float64):
        return 9
    elif (
        numpy_dtype == bool
    ):  # numpy uses regular python bool type so type check is different
        return 10
    elif numpy_dtype.kind == "S":  # byte strings
        return 11
    elif numpy_dtype.kind == "U":  # Unicode strings
        return 12
    else:
        raise ValueError(
            "Provided ndarray must be one of the following datatypes: int/uint(8, 16, 32, 64), float(16, 32, 64), boolean, fixed-length or variable-length strings."
        )


def _get_internal_dtypes(dtypes):
    internal_types = []
    for dtype in dtypes:
        internal_types.append(_get_internal_dtype(dtype))
    return internal_types


def _get_dtype_sizes(dtypes):
    sizes = []
    for dtype in dtypes:
        if isinstance(dtype, np.dtype):
            sizes.append(dtype.itemsize)
        else:
            sizes.append(0)
    return sizes


def _get_unit_as_string(unit):
    if type(unit) == str:
        # verify that provided string is in a valid FITS unit format
        try:
            converted = units.Unit(unit)
            return unit
        except:
            raise ValueError(
                "Provided unit must be either an astropy.units instance or a valid FITS-formatted unit string."
            )
    else:
        try:
            return FITS.to_string(unit)
        except:
            raise ValueError(
                "Provided unit must be either an astropy.units instance or a valid FITS-formatted unit string."
            )


def _get_units_as_strings(units):
    if type(units) == list:
        strings = []
        for unit in units:
            strings.append(_get_unit_as_string(unit))
        return strings
    else:
        return [_get_unit_as_string(units)]


def _get_expected_num_units(info):
    count = 0
    if type(info) == list or type(info) == tuple:
        for i in range(len(info)):
            count += _get_num_datasets(info[i])
    else:
        count += _get_num_datasets(info)
    return count


def _get_num_datasets(dset):
    if isinstance(dset, np.ndarray) and dset.dtype.names is not None:
        return len(dset.dtype.names)
    elif isinstance(dset, pd.DataFrame):
        return len(dset.columns)
    elif isinstance(dset, Table):
        return len(dset.colnames)
    else:
        return 1


def _verify_parameters(info, object_name, data_names, data_units):
    if object_name != None:
        if type(object_name) != str:
            raise ValueError(
                "Given object name is not in an acceptable format (must be a string)."
            )

    if data_names != None:
        if type(data_names) != list and type(data_names) != str:
            raise ValueError(
                "Given data names are not in an acceptable format (must be a single string or list of strings)."
            )
        if (
            type(data_names) == list
            and len(data_names) > 0
            and not all(isinstance(item, str) for item in data_names)
        ):
            raise ValueError(
                "Given data names are not in an acceptable format (must be a single string or list of strings)."
            )
        if isinstance(info, list) or isinstance(info, tuple):
            if len(data_names) != len(info):
                raise ValueError(
                    f"Number of data names ({len(data_names)}) does not match the number of datasets ({len(info)})."
                )
        else:
            if (
                type(data_names) != str
                and type(data_names) == list
                and len(data_names) != 1
            ):
                raise ValueError(
                    "Multiple data names given but only one dataset provided."
                )

    if data_units != None:
        num_units = _get_expected_num_units(info)
        _get_units_as_strings(data_units)

        if (len(data_units) if type(data_units) == list else 1) != num_units:
            raise ValueError(
                f"Number of data units ({len(data_units) if type(data_units) == list else 1}) does not match the expected number ({num_units})."
            )


## Data deserialization


def _deserialize_data(data, dims, dtype):
    try:
        # convert to numpy array based on data info
        flat = np.frombuffer(data, dtype=_get_numpy_dtype(dtype))
        reshaped = flat.reshape(tuple(dims))
        return reshaped
    except:
        raise ValueError("Received server data not in acceptable format.")


def _get_numpy_dtype(internal_type):
    return np.float32
