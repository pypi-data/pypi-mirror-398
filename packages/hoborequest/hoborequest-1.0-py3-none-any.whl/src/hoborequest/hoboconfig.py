#!/usr/bin/env python3

"""
HOBO-config:
Creates or updates HDF files for HOBO-request

See LICENSE and AUTHORS for more info
"""

import sys
import os
import yaml
import logging
import numpy as np
import h5pyd
import h5py

from datetime import datetime

if __name__ == "__main__":
    from lib.hobo_dtype import dt_logger, dt_sensor, dt_measurements
    from lib.hobo_metadata import update_general, update_logger, update_sensor
else:
    from .lib.hobo_dtype import dt_logger, dt_sensor, dt_measurements
    from .lib.hobo_metadata import update_general, update_logger, update_sensor


def usage():
    """Displays CLI help and usage instructions."""
    print("[HOBO-config] Create or update an HDF data file for HOBO-connect")
    print(
        "Usage: hobo-config.py [-h] [--loglevel debug|info|warning|error] <filepath> <config.yml>"
    )
    print("   <filepath>: HSDS or HDF5 file path ('hdf5://' prefix for HSDS)")
    print("   <config.yml>: Path to one or more HOBO config files")
    print("Options:")
    print("   --help: this message")
    print("   --loglevel debug|info|warning|error: change default log level")
    sys.exit(1)


def h5File(path, mode="r"):
    """Open an HSDS domain or HDF5 file based on the path.
       If path starts with "hdf5://", use HSDS, otherwise
       use h5py on a regular file path"""
    logging.debug(f"[HOBO-config] Opening h5File: '{path}', mode: '{mode}'")
    if path.startswith("hdf5://"):
        f = h5pyd.File(path, mode=mode, use_cache=False)
    else:
        f = h5py.File(path, mode=mode)
    return f


def create_table(grp, name, dt):
    """Create extensible 1-D dataset of given type if object with that
       name doesn't already exist."""
    if name in grp:
        return  # Dataset already exists
    logging.info(f"[HOBO-config] Creating dataset: {name}")

    grp.create_dataset(name, (0,), maxshape=(None,), dtype=dt)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        usage()

    yaml_filenames = []
    hdf_filepath = None

    loglevel = logging.INFO
    argn = 1
    while argn < len(sys.argv):
        arg = sys.argv[argn]
        val = None
        if len(sys.argv) > argn + 1:
            val = sys.argv[argn + 1]
        if arg[0] == "-":
            # process option
            if arg == "--loglevel":
                val = val.upper()
                if val == "DEBUG":
                    loglevel = logging.DEBUG
                elif val == "INFO":
                    loglevel = logging.INFO
                elif val in ("WARN", "WARNING"):
                    loglevel = logging.WARNING
                elif val == "ERROR":
                    loglevel = logging.ERROR
                else:
                    usage()
                argn += 1
            elif arg in ("-h", "--help"):
                usage()
            else:
                # unknown option
                usage()
        else:
            if not hdf_filepath:
                hdf_filepath = arg
            else:
                yaml_filenames.append(arg)
        argn += 1

    if not yaml_filenames:
        logging.warning("[HOBO-config] No YAML filenames provided")

    if not hdf_filepath:
        logging.error("[HOBO-config] HDF filepath not provided")
        usage()

    logging.basicConfig(format="%(asctime)s %(message)s", level=loglevel)

    if not os.path.isfile(hdf_filepath):
        logging.warning(
            f"[HOBO-config] HDF file: {hdf_filepath} not found, will initialize new file"
        )

    with h5File(hdf_filepath, mode="a") as h:
        logging.debug(f"Got root id: {h.id.id}")
        # Create loggers table if not created already
        create_table(h, "loggers", dt_logger)
        # Create sensors table if not created already
        create_table(h, "sensors", dt_sensor)
        # Create data table if not created already
        create_table(h, "data", dt_measurements)

        # Initalize/update groups and attributes from YAML file
        for filename in yaml_filenames:
            logging.info(f"[HOBO-config] Loading {filename}")
            if not os.path.isfile(filename):
                logging.warning(f"[HOBO-config] YAML file: {filename} not found, ignoring")
                continue
            with open(filename, "r") as f:
                yaml_config = None
                try:
                    yaml_config = yaml.safe_load(f)
                except yaml.scanner.ScannerError as se:
                    logging.error(
                        f"[HOBO-config] Error loading YAML file: {filename}: {se}"
                    )
                if yaml_config:
                    if "schema" not in yaml_config:
                        logging.warning(
                            f"[HOBO-config] No 'schema' key found in {filename}, ignoring"
                        )
                    else:
                        ts = np.uint32(datetime.utcnow().timestamp())
                        schema = yaml_config["schema"]
                        if schema == "hobo-general":
                            update_general(h, yaml_config)
                            h.attrs["last_updated_metadata"] = ts
                        elif schema == "hobo-logger":
                            update_logger(h, yaml_config)
                            h.attrs["last_updated_metadata"] = ts
                        elif schema == "hobo-sensor":
                            update_sensor(h, yaml_config)
                            h.attrs["last_updated_metadata"] = ts
                        else:
                            logging.warning(
                                f"[HOBO-config] Unknown schema: {schema}, ignoring {filename}"
                            )
        logging.info("[HOBO-config] Done!")

#
# Main
#
main()
