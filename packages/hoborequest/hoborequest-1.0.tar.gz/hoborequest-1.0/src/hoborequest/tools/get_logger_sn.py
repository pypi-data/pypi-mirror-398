#!/usr/bin/env python3

"""
HOBO-get-logger-sn:
Utility to display logger serial numbers

See LICENSE and AUTHORS for more info
"""

import sys
import datetime
import h5pyd

#
# standardize display format for logger field
#
def format_field(x):
    """Standardize display format for logger field."""
    if isinstance(x, bytes):
        x = x.decode("utf-8")
    elif isinstance(x, float):
        x = f"{x:.6f}"
    return x


#
# main routine
#
def main():
    """Display CLI help instructions."""
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("usage: python get_logger_sn.py <hobo_file> [logger_sn]")
        print("example: python get_logger_sn.py hdf5://projects/nsfarctic/uva_test.h5")
        sys.exit()
    filepath = sys.argv[1]

    if len(sys.argv) > 2:
        logger_sn = sys.argv[2]
    else:
        logger_sn = None

    f = h5pyd.File(filepath)

    logger_table = f["loggers"]

    if logger_sn:
        query = f"sn == b'{logger_sn}'"
        rows = logger_table.read_where(query)
        if len(rows) == 0:
            print(f"no logger entry for sn: {logger_sn}")
            sys.exit(1)
        if len(rows) > 1:
            print("got multiple rows for sn: {logger_sn}")
            sys.exit(1)
        row = rows[0]
        # read_where will return index of the row as first component
        colnames = [
            "index",
        ]
        indent = " " * 4
        colnames.extend(logger_table.colnames)
        print(f"logger {logger_sn}:")
        for i in range(len(row)):
            print(f"{indent}{colnames[i]}: {format_field(row[i])}")
        print("")
    else:
        # print all headers

        header = ""
        for colname in logger_table.colnames:
            header += f"{colname}\t"
        print(header)
        print("-" * 80)
        cursor = logger_table.create_cursor()
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
        sys.exit(0)

    # get list of logger sn's defined in the data table
    logger_sns = {}
    cursor = data_table.create_cursor()
    for row in cursor:
        logger_sn = row["logger_sn"].decode("ascii")
        timestamp = row["timestamp"]
        if logger_sn not in logger_sns:
            logger_sns[logger_sn] = [timestamp, timestamp]
        else:
            interval = logger_sns[logger_sn]
            if timestamp < interval[0]:
                interval[0] = timestamp
            if timestamp > interval[1]:
                interval[1] = timestamp

    print(f"logger count: {len(logger_sns)}")
    print("")

    print("   logger_sn     first_time    last_time")
    logger_list = list(logger_sns.keys())
    logger_list.sort()

    for logger_sn in logger_list:
        interval = logger_sns[logger_sn]
        dt_interval = ""
        for i in range(len(interval)):
            dt = datetime.datetime.utcfromtimestamp(interval[i])
            dt_interval += dt.isoformat(sep=" ", timespec="seconds")
            dt_interval += "   "
        print(f"   {logger_sn}  {dt_interval}")


#
# Main
#
main()
