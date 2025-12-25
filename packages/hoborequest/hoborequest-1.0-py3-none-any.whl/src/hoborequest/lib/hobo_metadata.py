"""
HOBO-metadata:
Creates or updates HDF metadata fields

See LICENSE and AUTHORS for more info
"""

import logging
import numpy as np


def compare(a, b):
    """Return true if the two attributes are the same
       Ignore small differences in floating point values."""

    TOLERANCE = 0.00001
    retval = a == b
    #
    # Comparison will return an array of booleans if a is an ndarray
    # Return True only if all values match
    #
    if isinstance(retval, np.ndarray):
        return retval.all()
    elif isinstance(a, float) or isinstance(a, np.float32) or isinstance(a, np.float64):
        if abs(a - b) < TOLERANCE:
            return True
        else:
            return False
    else:
        return retval


def update_logger(grp, keystore):
    """Given a HDF group and keystore, update or append to the loggers table.
       If a logger exist with the same serial number ('sn' key), that row will
       be updated. Otherwise a new row will be added to the table."""

    if "loggers" not in grp:
        logging.error(
            f"[HOBO-metadata] Expected to find 'loggers' table in group {grp.name}"
        )
        return 0
    dset = grp["loggers"]

    if "sn" not in keystore:
        logging.error("[HOBO-metadata] Expected to find key 'sn' in keystore")
        return 0
    sn = keystore["sn"]

    #
    # Load the entire table
    # Note: this will be fairly efficient for up to several thousand rows
    #
    loggers = dset[()]
    row_id = None
    num_rows = loggers.shape[0]
    for i in range(num_rows):
        logger = loggers[i]
        logger_sn = logger["sn"].decode("utf-8")  # bytestring to str
        if logger_sn == str(sn):
            logging.info(
                f"[HOBO-metadata] Found serial number {sn} in loggers row[{i}]"
            )
            row_id = i
            break

    if row_id is None:
        # Append to the loggers table
        logging.info(f"[HOBO-metadata] Adding new logger with serial number: {sn}")
        dset.resize((num_rows + 1,))
        row_id = num_rows
    logger = dset[row_id]
    count = 0

    for k in keystore:
        if k == "schema" or k == "last_query":
            continue
        v = keystore[k]
        if type(v) == int:
            v = str(v)
        #
        # Convert from np.bytestring to str, if needed
        # before comparing values
        #
        try:
            k_val = logger[k].decode("utf-8")
        except (UnicodeDecodeError, AttributeError, ValueError):
            k_val = logger[k]
        if not compare(k_val, v):
            logging.info(
                f"[HOBO-metadata] Changing logger key '{k}' from: {k_val} to: {v}"
            )
            logger[k] = v
            count += 1

    if count > 0:
        logging.info(f"[HOBO-metadata] Updating logger {sn} at row: {row_id}")
        # Write to dataset
        dset[row_id] = logger
    else:
        logging.info(f"[HOBO-metadata] No changes for logger {sn}")
    return count


def update_sensor(grp, keystore):
    """Given a HDF group and keystore, update or append to the sensor table.
       If a sensor exist with the same serial number ('sn' key), that row will
       be updated. Otherwise a new row will be added to the table."""

    if "sensors" not in grp:
        logging.error(
            f"[HOBO-metadata] Expected to find 'sensors' table in group {grp.name}"
        )
        return 0
    dset = grp["sensors"]

    if "sn" not in keystore:
        logging.error("[HOBO-metadata] Expected to find key 'sn' in keystore")
        return 0
    sn = keystore["sn"]

    #
    # Load the entire table
    # Note: this will be fairly efficient for up to several thousand rows
    #
    sensors = dset[()]
    row_id = None
    num_rows = sensors.shape[0]
    count = 0  # number of updated/added sensors
    for i in range(num_rows):
        sensor = sensors[i]
        sensor_sn = sensor["sn"].decode("utf-8")
        if sensor_sn == sn:
            logging.info(
                f"[HOBO-metadata] Found serial number {sn} in 'sensors' row[{i}]"
            )
            row_id = i
            break

    if row_id is None:
        # Append to the table
        logging.info(f"[HOBO-metadata] Adding new sensor with serial number: {sn}")
        dset.resize((num_rows + 1,))
        row_id = num_rows
    sensor = dset[row_id]

    for k in keystore:
        if k == "schema":
            continue  # Ignore 1st line of YAML file
        v = keystore[k]
        if v is None:
            continue
        if type(v) == int:
            v = str(v)
        try:
            k_val = sensor[k].decode("utf-8")
        except (UnicodeDecodeError, AttributeError):
            k_val = sensor[k]
        if not compare(k_val, v):
            logging.info(
                f"[HOBO-metadata] Changing sensor key '{k}' from: {k_val} to: {v}"
            )
            sensor[k] = v
            count += 1

    if count > 0:
        logging.info(f"[HOBO-metadata] Updating sensor {sn} at row: {row_id}")
        dset[row_id] = sensor  # Write to dataset
    else:
        logging.info(f"[HOBO-metadata] No changes for sensor {sn}")
    return count


def update_general(grp, keystore):
    """Given a HDF group and keystore create attributes for keystore
       values and subgroups for keystore dicts. Recurse as needed."""

    logging.debug(
        f"[HOBO-metadata] Update_general for group '{grp.name}' with {len(keystore)} items"
    )
    count = 0  # number of updated keys

    for k in keystore:
        v = keystore[k]
        logging.debug(f"[HOBO-metadata] Key: {k}")
        if isinstance(v, dict):
            #
            # Verify there's a sub-group with name k
            # Create if not
            #
            if k not in grp:
                logging.info(f"[HOBO-metadata] Creating subgroup: {k}")
                subgroup = grp.create_group(k)
            else:
                # TBD: verify this is actually a group
                subgroup = grp[k]
            count += update_general(subgroup, v)
        else:
            if isinstance(v, str) and len(v) > 8:
                abbrv = v[:8] + "..."
            else:
                abbrv = v
            # Check if attribute with name k exists
            if k not in grp.attrs:
                # Create an attribute with name k, value v
                logging.info(
                    f"[HOBO-metadata] Creating attribute '{k}' with value: {abbrv}"
                )
                grp.attrs[k] = v
                count += 1
            else:
                #
                # Update attribute if current value is different
                # Bypass if it is a value that is set by hobo-connect
                # E.g. 'last_updated_data' and 'last_updated_metadata'
                #
                current = grp.attrs[k]
                if not compare(v, current):
                    if k == "last_updated_data" or k == "last_updated_metadata":
                        logging.debug(f"[HOBO-metadata] By-passing '{k}' field")
                        pass
                    else:
                        logging.info(
                            f"[HOBO-metadata] Updating attribute '{k}' with value: {abbrv}"
                        )
                        del grp.attrs[k]
                        grp.attrs[k] = v
                        count += 1
    return count
