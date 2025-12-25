#!/usr/bin/env python3

"""
HOBO-check-dups:
Verifies with duplicated rows exist in the HSDS

See LICENSE and AUTHORS for more info
"""

import sys
import h5pyd

BLOCK_SIZE = 1000


def check_dups(data_table, sensor_map):
    start = 0
    stop = 0
    while start < data_table.nrows:
        start = stop
        stop = start + BLOCK_SIZE
        if stop > data_table.nrows:
            stop = data_table.nrows
        # print(f"reading rows {start}:{stop}")
        arr = data_table[start:stop]
        for i in range(len(arr)):
            row = arr[i]
            rownum = i + start
            timestamp = row["timestamp"]
            if len(row["sensor_sn"]) == 0:
                print(f"empty row: {rownum}")
            else:
                sensor_sn = row["sensor_sn"].decode("ascii")

                if sensor_sn not in sensor_map:
                    print(f"found new sensor: {sensor_sn}")
                    sensor_map[sensor_sn] = {}
                ts_map = sensor_map[sensor_sn]
                timestamp = row["timestamp"]
                if timestamp in ts_map:
                    dup_row = ts_map[timestamp]
                    print(f"row: {rownum} is a dup of row: {dup_row}")
                else:
                    ts_map[timestamp] = rownum


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("usage: python check_dups.py <hobo_file>")
        print("example: python check_dups.py hdf5://projects/nsfarctic/uva_test.h5")
        sys.exit()
    filepath = sys.argv[1]
    f = h5pyd.File(filepath)

    data_table = f["data"]

    sensor_map = {}
    check_dups(data_table, sensor_map)

    # get list of sensor sn's defined in the sensor table
    sensor_table = f["sensors"]
    sensor_sns = set()
    cursor = sensor_table.create_cursor()
    for row in cursor:
        sensor_sn = row["sn"].decode("ascii")
        sensor_sns.add(sensor_sn)

    # list sensor counts from sensor map
    print("=====================")
    print(f"{len(sensor_map)} sensors found")
    for sensor_sn in sensor_map:
        ts_map = sensor_map[sensor_sn]
        line = f"{sensor_sn}: {len(ts_map)} entries"
        if sensor_sn not in "sensor_sns":
            line += " MISSING"
        print(line)


#
# main
#
main()
