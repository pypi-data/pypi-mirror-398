#!/usr/bin/env python3

"""
HOBO-get-sensor-sn:
Utility to display serial sensor numbers

See LICENSE and AUTHORS for more info
"""

import sys
import datetime
import h5pyd

#
# Standardize display format for sensor field
#
def format_field(x):
    """Standardize the display format for the sensor field"""
    if isinstance(x, bytes):
        x = x.decode("utf-8")
    elif isinstance(x, float):
        x = f"{x:.6f}"
    return x


#
# Main routine
#
def main():
    """Display CLI help instructions."""
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("usage: python get_sensor_sn.py <hobo_file> [logger_sn]")
        print("example: python get_sensor_sn.py hdf5://projects/nsfarctic/uva_test.h5")
        sys.exit()
    filepath = sys.argv[1]

    if len(sys.argv) > 2:
        sensor_sn = sys.argv[2]
    else:
        sensor_sn = None

    f = h5pyd.File(filepath)

    sensor_table = f["sensors"]

    if sensor_sn:
        query = f"sn == b'{sensor_sn}'"
        rows = sensor_table.read_where(query)
        if len(rows) == 0:
            print(f"no sensor entry for sn: {sensor_sn}")
            sys.exit(1)
        if len(rows) > 1:
            print("got multiple rows for sn: {sensor_sn}")
            sys.exit(1)
        row = rows[0]
        # read_where will return index of the row as first component
        colnames = [
            "index",
        ]
        indent = " " * 4
        colnames.extend(sensor_table.colnames)
        print(f"sensor {sensor_sn}:")
        for i in range(len(row)):
            print(f"{indent}{colnames[i]}: {format_field(row[i])}")
        print("")
    else:
        # print all headers

        header = ""
        for colname in sensor_table.colnames:
            header += f"{colname}\t"
        print(header)
        print("-" * 80)
        cursor = sensor_table.create_cursor()
        for row in cursor:
            line = ""
            for item in row:
                item = format_field(item)
                line += f"{item}\t"
            print(line)
        print("")

    data_table = f["data"]
    if len(data_table) == 0:
        print("no data found!")

    # get list of sensor sn's defined in the data table
    sensor_sns = {}
    cursor = data_table.create_cursor()
    for row in cursor:
        sensor_sn = row["sensor_sn"].decode("ascii")
        timestamp = row["timestamp"]
        if sensor_sn not in sensor_sns:
            sensor_sns[sensor_sn] = [timestamp, timestamp]
        else:
            interval = sensor_sns[sensor_sn]
            if timestamp < interval[0]:
                interval[0] = timestamp
            if timestamp > interval[1]:
                interval[1] = timestamp

    print(f"sensor count: {len(sensor_sns)}")
    print("")

    print("   sensor_sn     first_time    last_time")
    sensor_list = list(sensor_sns.keys())
    sensor_list.sort()

    for sensor_sn in sensor_list:
        interval = sensor_sns[sensor_sn]
        dt_interval = ""
        for i in range(len(interval)):
            dt = datetime.datetime.utcfromtimestamp(interval[i])
            dt_interval += dt.isoformat(sep=" ", timespec="seconds")
            dt_interval += "   "
        print(f"   {sensor_sn}  {dt_interval}")


#
# Main
#
main()
