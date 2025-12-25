# HOBO-request

A Kubernetes-ready container application for integrating HOBOlink loggers with HSDS.

## Getting started

HOBO-request provides an interface to HOBOlink loggers via a public API that is provided by Onset.
It can be used with HSDS for the purposes of large-scale environmental data management, or as a stand-alone
tool for the purposes of testing. It can also be easily extended to be used with different APIs and sensor
networks.

You can install the HOBO-request package or git clone this repository. For installing the pip package,
just create a virtual environmental and run:

```bash
$ python3 -m venv hobo-request
$ source hobo-request/bin/activate
$ pip install hoborequest
```

HOBO-request is now ready to be used, but first it must be configured!

## Configuration

First, copy `conf/hobo-connect.conf-SAMPLE` to `conf/hobo-connect.conf`.
Then, edit `conf/hobo-connect.conf` and set the following parameters:

* `token`: your Onset API token
* `start_date_time`: for precise time slicing, the start time in UTC, format: 2012-01-01 23:00:00
* `end_date_time`: same as above, the end time in UTC, format: 2021-01-12 11:00:00
* `polling_interval_minutes`: if you want to set a regular polling interval, leave start & end time fields empty.
Alternatively you can also set a start time, but leave end time empty.

Please observe that timestamps are always assumed to be in UTC. For the purposes of data storage, it is more 
convenient to avoid timezones and daylight-saving differences, and leave to the analyst to manipulate
timestamps as he/she/they see fit.

In addition to the configuration of your Onset credentials, you also need to set your HSDS parameters:

* `hsds_filename`: your HDF datastore file name
* `hsds_endpoint`: your HSDS endpoint

Please observe that you can also use HOBO-request locally without HSDS. In that case, you only
need to set `hsds_filename` to point to the HDF5 file in your local filesystem. 
 
Finally, you must set the repository where your logger and sensor metadata are registered. This is a crucial step
because HOBO-request depends on this config to update your metadata attributes for you automagically. 

You must set the following fields:

* `meta_repo`: git repository that contains your deployment metadata files
* `meta_local_dir`: local directory where you want to store the repo temporarily
* `meta_root_path`: repository directory where the HDF root file metadata file is
* `meta_loggers_dir`: repository directory where the loggers metadata files are located
* `meta_sensors_dir`: repository directory where the sensors metadata files are located

Once this is all done, we can move on to the generation of your HDF data store.

## Creating your HDF data store with metadata

HOBO-request reads YAML files with metadata organized in three levels:

* `HDF root metadata` (attributes)
* `HOBO loggers` (attributes)
* `HOBO sensors` (attributes)

It is necessary, therefore, to create YAML files following the schema we describe in the `conf/` and 
`conf/sensors/templates` directories. For example:

* `uva-arc.yaml`: provides an example of how to set root attributes in your HDF file
* `loggers/`: provides examples for the configuration of HOBOLink loggers / stations
* `sensors/templates`: provides examples for the configuration of HOBOLink sensors

Once you are done creating your YAML files, you can load them in your newly created HDF file.
Change directory to `src/`, then run `hobo-config.py`:

To generate your HDF file with root attributes, you can run the following commands:

```bash
$ hoboconfig test.h5 ../conf/uva-arc.yaml
```

Please note that you have to change the PATH for the YAML file in the command above.
You can find real examples for stations and sensors in [this repository.](https://gitlab.com/uva-arc/deployment-metadata)

To load your logger and sensor metadata, you just need to specify where you YAML files are:

```bash
$ hoboconfig test.h5 /tmp/your-metadata-files/YAML/loggers/*
$ hoboconfig test.h5 /tmp/your-metadata-files/YAML/sensors/*
```

Please note that it is necessary to run this step only **once** when creating the HDF data store.

After you load the HDF file onto HSDS, HOBO-request will automatically pull all the changes
from the `git` repository containing your YAML files and load all the metadata information
for you. There is no need to use `hobo-config` manually again. The same applies for locally
generated HDF5 files. Your local file will be updated if changes in the metadata repository
are detected.

## Running HOBO-request to retrieve sensor data

Now that everything is in place, you have the choice of running HOBO-request locally for tests
using a regular HDF file (and h5py) or run the HDF data store on HSDS (with h5pyd). This is 
done automagically for you, so you just have to point in your config file if you want to use
a regular file or interface with HSDS to feed data to your HDF data store.

You can start HOBO-request with a simple command:

```bash
$ hoboconnect
```

The application will output the following status messages, so you can follow the processing steps:

```bash
HOBO-log] Starting up hoboconnect
[HOBO-log] Setting up logging parameters
[HOBO-log] Starting INFO logging
[HOBO-connect] Start: 2025-07-01 08:00:00 UTC
[HOBO-connect] Time slice: 2025-07-01 08:00:00 --> 
[HOBO-connect] Using polling interval: 1 minute(s)
[HOBO-metadata] Starting metadata verification
[HOBO-metadata] Using metadata repository: https://gitlab.com/uva-arc/deployment-metadata
[HOBO-metadata] Metadata repository name: deployment-metadata
...
[HOBO-metadata] Creating attribute 'schema' with value: hobo-gen...
[HOBO-metadata] Creating attribute 'schema_version' with value: 0.1
[HOBO-metadata] Creating attribute 'Conventions' with value: CF-1.8
[HOBO-metadata] Creating attribute 'title' with value: NSF Proj...
[HOBO-metadata] Creating attribute 'institution' with value: U. of Vi...
[HOBO-metadata] Creating attribute 'source' with value: surface ...
...
[HOBO-log] Logger: 21198259
[HOBO-log] Query start time: 2025-07-01 08:00:00, end time: 2025-07-02 08:00:00
[HOBO-log] Timestamp: 2025-07-02 08:00:00 >= query_end_date_time, stop row iteration
[HOBO-log] Got 2324 update rows
[HOBO-log] Current data table shape: 0, adding: 2324
[HOBO-log] ---> Data processing completed for logger 21198259, 2324 data point(s) added
[HOBO-log] Logger: 21401800
[HOBO-log] Query start time: 2025-07-01 08:00:00, end time: 2025-07-02 08:00:00
[HOBO-log] No rows found in data
[HOBO-log] Got 0 update rows
[HOBO-log] ---> Data processing completed for logger 21401800, 0 data point(s) added
[HOBO-log] Logger 21401800: not caught up to 2025-12-23 04:36:26.528814 yet
[HOBO-log] Logger: 21401801
[HOBO-log] Query start time: 2025-07-01 08:00:00, end time: 2025-07-02 08:00:00
[HOBO-log] Timestamp: 2025-07-02 08:00:00 >= query_end_date_time, stop row iteration
[HOBO-log] Got 2928 update rows
[HOBO-log] Current data table shape: 2324, adding: 2928
[HOBO-log] ---> Data processing completed for logger 21401801, 2928 data point(s) added
```

Data processing occurs through a series of steps: first, your HDF5 file is opened and verified,
metadata is checked against the repository (for updates) and, then, data is processed in batches
(following sane parameters to avoid timeouts, set in the conf file), iterating over every 
environmental field station (logger) and every sensor (as shown in the example above).

Once data processing is done, you will see the following message:

```bash
[HOBO-log] Done: exiting
```

Et voilà! Now you have all your environmental data organized with good metadata, something that
HOBO does not provide through their API.

## Development instructions

So, you want to help us improve `hobo-request`? We are glad!

You can get started by cloning this Git repository, creating a virtual environment and installing
the dependencies we have for `hobo-request`. Just run the following commands:

```bash
$ python3 -m venv hobo-request
$ git clone https://gitlab.com/uva-arc/hobo-request.git
$ pip install -f requirements.txt
```

Tp build the hobo-request package run the following commands:

```bash
$ python -m venv hobo-request
$ pip install build
$ python -m build
$ pip install -v .
```

### Generating a container for HOBO-request

We have provided scripts and deployment files to generate a container for HOBO-request, plus 
documentation on how to run HSDS on k3s (or microk8s) for local testing.

You can run the following commands to build your container and run it:

```bash
$ ./build.sh
$ ./docker_run.sh
```

The directory `k8s` contains the deployment files and scripts for running HOBO-request on k8s or microk8s.

May the source be with you in your environmental studies!

## Licensing

See LICENSE and AUTHORS files for details.

## Acknowledgement

This application was developed in partnership with the HDF Group and funded by the National Science Foundation (grant #2022639).

