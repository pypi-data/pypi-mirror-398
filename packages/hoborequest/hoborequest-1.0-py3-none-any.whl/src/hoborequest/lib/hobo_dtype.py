"""
HOBO-dtype:
Describes the data types to be used by the HDF store

See LICENSE and AUTHORS for more info
"""

import numpy as np
import h5py

#
# Definition of data types (dt)
#
# Standard type for variable length unicode strings
# Note: generally want to use these only for smaller datasets,
#       since it is not as efficient as fixed-length types.
#       This is used for metadata attributes here.
dt_vlen = h5py.special_dtype(vlen=str)

# Type for storing sensor serial numbers
# Note: HOBO API uses 12 characters for serial number.
dt_sn = np.dtype('S16')

# Type for storing unit specification (m, A, v, etc.)
# Note: HOBO API uses UTF-8, so do we.
dt_unit = h5py.special_dtype(vlen=str)

# Type for storing lat/lon/height coordinates
# Note: we use 5-decimal point precision, 'float32'.
dt_geo = np.dtype('f8')

# Type for storing boolean values
# Note: using one byte int for HDF compat.
dt_bool = np.dtype('i1')

# Type for measurement data
# Note: HOBO API uses float64, so do we.
dt_data = np.dtype('f8')

# Type for enumerated values (e.g. measurement type)
dt_enum = np.dtype('i2')

# Type for timestamps
dt_time = np.dtype('u4')
# Note: we follow the CF standard definition + Unix epoch:
#  "seconds since 1970-01-01 00:00:00"
# Note: measures UTC seconds in epoch
# Note: using string timestamps (e.g. "11-07-21 05:35:00Z", requires
#       more storage and is not efficent for querying specific time ranges)
# TBD: signed value will overflow in 2038-01-19
#      or if uint32, overflow will happen in 2102
#      or use 8-byte timestamp (safe for many billion years)

# Datatype for 'loggers' table
dt_logger = np.dtype([('sn', dt_sn),
                      ('schema_version', dt_data),
                      ('active', dt_bool),
                      ('name', dt_vlen),
                      ('name_ipk', dt_vlen),
                      ('model', dt_vlen),
                      ('location_en', dt_vlen),
                      ('location_ipk', dt_vlen),
                      ('lat', dt_geo),
                      ('lat_units', dt_unit),
                      ('lon', dt_geo),
                      ('lon_units', dt_unit),
                      ('height', dt_geo),
                      ('height_units', dt_unit),
                      ('altitude', dt_geo),
                      ('altitude_units', dt_unit),
                      ('battery_level_max', dt_data),
                      ('battery_level_min', dt_data),
                      ('battery_units', dt_unit),
                      ('last_query', dt_time)])


# datatype for 'sensors' table
dt_sensor = np.dtype([('sn', dt_sn),
                      ('sn_logger', dt_sn),
                      ('schema_version', dt_data),
                      ('active', dt_bool),
                      ('long_name', dt_vlen),
                      ('standard_name', dt_vlen),
                      ('sensor_type', dt_vlen),
                      ('model', dt_vlen),
                      ('lat', dt_geo),
                      ('lat_units', dt_unit),
                      ('lon', dt_geo),
                      ('lon_units', dt_unit),
                      ('height', dt_geo),
                      ('height_units', dt_unit),
                      ('angle', dt_data),
                      ('angle_units', dt_unit),
                      ('altitude', dt_geo),
                      ('altitude_units', dt_unit),
                      ('mount_structure', dt_vlen),
                      ('mount_aspect', dt_vlen),
                      ('mount_corner', dt_bool),
                      ('convergence', dt_bool),
                      ('battery_level_max', dt_data),
                      ('battery_level_min', dt_data),
                      ('battery_units', dt_unit),
                      ('accuracy', dt_vlen),
                      ('resolution', dt_vlen),
                      ('drift', dt_vlen),
                      ('datasheet', dt_vlen),
                      ('measurement_type', dt_vlen),
                      ('measurement_min', dt_data),
                      ('measurement_max', dt_data),
                      ('measurement_units', dt_unit),
                      ('missing_values', dt_data)])


# datatype for 'data' table
dt_measurements = np.dtype([('logger_sn', dt_sn),
                            ('sensor_sn', dt_sn),
                            ('data_type_id', dt_enum),
                            ('measurement_type', dt_enum),
                            ('value', dt_data),
                            ('timestamp', dt_time)])

