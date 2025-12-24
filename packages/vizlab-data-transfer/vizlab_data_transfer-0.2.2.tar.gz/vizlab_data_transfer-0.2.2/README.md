# vizlab-data-transfer
[![Run Python tests](https://github.com/carnegie/vizlab-data-transfer/actions/workflows/run-tests.yaml/badge.svg?branch=main)](https://github.com/carnegie/vizlab-data-transfer/actions/workflows/run-tests.yaml) ![Coverage Status](/badges/coverage-badge.svg?dummy=8484744)

This package enables easy transferring of data to and from the VizLab! 

## How to set up

To use this package, we need a proper connection to Carnegie's local network. You can do this in a couple ways:

* By using a Carnegie-managed device connected to the CarnegieEmployees network
* By logging in with your Carnegie VPN

You'll need to set the VizLab local IP and appropriate port number - look to internal Carnegie resources for these:

```
from vizlab_data_transfer import vizlab

# set network state
vizlab.set_ip(IP)
vizlab.set_port(PORT)

# get network state
print(vizlab.get_ip())
print(vizlab.get_port())
```

These values are stored internally by the package and persist between sessions, so set them once and you're good to go!

## How to use

This package is designed to be as straightforward as possible. To send Python data to the system, use the ```vizlab.send()``` method:

```
from vizlab_data_transfer import vizlab

vizlab.send(data) # give a single dataset
vizlab.send([table, fig1, fig2]) # or a list of them...
```

You can also use optional arguments to send additional details about your data:

```
from vizlab_data_transfer import vizlab

vizlab.send([positions, lum], object_name = "stellarstream-results", data_names = ["xyz_pos", "luminosity"]) # provide additional data details

vizlab.send(radii, object_name = "stellarstream-results", data_names = "disk_radii") # give the same object name to append data to an existing object in the system
```

Currently we support a variety of Python objects:
* numpy ndarrays and recarrays
* astropy FITS Table and ImageHDU objects
* matplotlib figures
* pandas dataframes
* Pillow images

Special notice must be taken for heteregeneous data sources (FITS tables, pandas dataframes, numpy recarrays) and specifying data names and units. You give a name for the table (the column names are already included in the data itself) and units for each column individually:

```
# recarray names/units example
vizlab.send(three_col_recarray, data_names=["table"], data_units = ["m", "s", "J"])
```

Feel free to leave an issue on this repository if there's a Python object you'd like support for!

Likewise, to receive data back from the system use ```vizlab.receive()```:

```
from vizlab_data_transfer import vizlab

# NOTE: VizLab must be in 'receive' state before this is run so server is ready to meet this request
data = vizlab.receive() 
```

Currently only numeric data of type ```np.float32``` can be returned.

Please consult the examples folder for more detailed use-cases!