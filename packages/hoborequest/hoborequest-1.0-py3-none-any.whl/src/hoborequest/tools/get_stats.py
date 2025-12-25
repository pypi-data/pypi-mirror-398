#!/usr/bin/env python3

"""
HOBO-get-stats:
Displays stats for a given HDF data store in HSDS

See LICENSE and AUTHORS for more info
"""

import sys
import datetime
import h5pyd


def do_data_scan(data_table):
    """Perform data scan on a data table."""
    cursor = data_table.create_cursor()

    first_timestamp = None
    last_timestamp = None
    month_counts = {}
    sensor_counts = {}
    for row in cursor:
        timestamp = row["timestamp"]
        if not timestamp:
            print("empty row!")
            continue
        if first_timestamp is None or timestamp < first_timestamp:
            first_timestamp = timestamp
        if last_timestamp is None or timestamp > last_timestamp:
            last_timestamp = timestamp
        dt = datetime.datetime.utcfromtimestamp(timestamp)
        yr_m = f"    {dt.year}.{dt.month:02d}"
        if yr_m not in month_counts:
            month_counts[yr_m] = 0
        month_counts[yr_m] += 1
        sensor_sn = row["sensor_sn"].decode("ascii")
        if yr_m not in sensor_counts:
            sensor_counts[yr_m] = set()
        sensor_counts[yr_m].add(sensor_sn)

    print("row count by month:")
    month_list = list(month_counts.keys())
    month_list.sort()
    for yr_m in month_list:
        print(f"{yr_m}: {month_counts[yr_m]}")
    print(" ")

    print("sensor count by month:")
    sensor_list = list(sensor_counts.keys())
    sensor_list.sort()
    for yr_m in sensor_list:
        print(f"{yr_m}: {len(sensor_counts[yr_m])}")
    print(" ")

    dt = datetime.datetime.utcfromtimestamp(first_timestamp)
    s = dt.isoformat(sep=" ", timespec="seconds")
    print(f"first entry: {s}")
    dt = datetime.datetime.utcfromtimestamp(last_timestamp)
    s = dt.isoformat(sep=" ", timespec="seconds")
    print(f"last entry:  {s}")


def main():
    """Display CLI help instructions."""
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("usage: python get_stats.py <hobo_file> [--noscan]")
        print("example: python get_stats.py hdf5://projects/nsfarctic/uva_test.h5")
        print("use --noscan option to skip scanning the data table")
        print("")
        sys.exit()
    filepath = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == "--noscan":
        scan_data = False
    else:
        scan_data = True

    f = h5pyd.File(filepath)

    logger_table = f["loggers"]
    logger_sns = set()
    cursor = logger_table.create_cursor()
    print("loggers")
    print("sn       \tlast_query")
    for row in cursor:
        logger_sn = row["sn"].decode("ascii")
        last_timestamp = row["last_query"]
        dt = datetime.datetime.utcfromtimestamp(last_timestamp)
        s = dt.isoformat(sep=" ", timespec="seconds")
        print(f"{logger_sn}\t{s}")
        logger_sns.add(logger_sn)

    print(f"logger count: {len(logger_sns)}")
    print("")

    # get list of sensor sn's defined in the sensor table
    sensor_table = f["sensors"]
    sensor_sns = set()
    cursor = sensor_table.create_cursor()
    for row in cursor:
        sensor_sn = row["sn"].decode("ascii")
        sensor_sns.add(sensor_sn)

    print(f"sensor count: {len(sensor_sns)}")
    print("")

    data_table = f["data"]
    if len(data_table) == 0:
        print("no data found!")
        return

    print(f"total rows: {len(data_table)}")
    print("")

    if scan_data:
        do_data_scan(data_table)


#
# Main
#
main()
