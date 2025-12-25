#!/usr/bin/env python3

"""
HOBO-check-gaps:
Verifies if gaps exist in the HSDS data store

See LICENSE and AUTHORS for more info
"""

import datetime
import sys
import h5pyd

MAX_TIME_DELTA = 3600  # largest time gap to report

# convert timestamp to a string
def ts_to_str(ts):
    value = datetime.datetime.utcfromtimestamp(ts)
    s = value.isoformat(sep=" ", timespec="seconds")
    return s


def check_gaps(data_table, sensor_sn=None):
    # check for gaps in the timestamp
    ts_last = None
    ts_high = None
    ts_low = None
    index = 0
    count = 0
    out_lines = 0
    gaps = []
    cursor = data_table.create_cursor()
    for row in cursor:
        ts = row["timestamp"]
        index += 1
        if ts <= 0:
            print(f"invalid ts row: {index}")
            out_lines += 1
            break
        if sensor_sn and row["sensor_sn"].decode("ascii") != sensor_sn:
            continue  # skip

        count += 1

        if ts_last is None:
            ts_last = ts
            ts_high = ts
            ts_low = ts
            continue

        if ts == ts_last:
            continue
        if ts_low > ts:
            ts_low = ts
        if ts_high < ts:
            ts_high = ts
        if ts < ts_last:
            # print(f"invalid order ts: {ts} ts_last: {ts_last} row: {index}")
            ts_last = ts
            continue
        if ts < ts_high:
            continue
        ts_delta = ts - ts_last
        if ts_delta > MAX_TIME_DELTA:
            gaps.append((ts_last, ts))
        ts_last = ts

    if ts_low is not None:
        print(f"time start: {ts_to_str(ts_low)}")
    if ts_high is not None:
        print(f"time end: {ts_to_str(ts_high)}")
    print(f"{count} rows found")

    num_gaps = len(gaps)
    print(f"number of gaps: {num_gaps}")

    cursor = data_table.create_cursor()  # reset cursor
    ts_last = None
    for row in cursor:
        ts = row["timestamp"]
        if ts_last is None:
            ts_last = ts
        if ts == ts_last:
            continue
        for i in range(num_gaps):
            gap = list(gaps[i])
            if ts > gap[0] and ts < gap[1]:
                # print(f"ts: {ts} found for gap[{i}]")
                # close up the gap on the smaller side
                if ts - gap[0] > gap[1] - ts:
                    gap[1] = ts
                else:
                    gap[0] = ts
                gaps[i] = gap

    gap_count = 0
    for gap in gaps:
        if gap[1] - gap[0] > MAX_TIME_DELTA:
            print(
                f"time gap: {gap[1]-gap[0]:6} seconds {ts_to_str(gap[0])} to {ts_to_str(gap[1])}"
            )
            gap_count += 1
    print(f"done: {gap_count} gaps")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("usage: python check_gaps.py <hobo_file> [sensor_sn]")
        print("example: python  hdf5://projects/nsfarctic/uva_test.h5")
        sys.exit()
    filepath = sys.argv[1]
    if len(sys.argv) > 2:
        sensor_sn = sys.argv[2]
    else:
        sensor_sn = None
    f = h5pyd.File(filepath)
    data_table = f["data"]
    check_gaps(data_table, sensor_sn=sensor_sn)


#
# main
#
main()
