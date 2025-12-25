#!/usr/bin/env python3

"""
HOBO-get-root-attrs:
Utility to display root attributes of HDF files

See LICENSE and AUTHORS for more info
"""

import sys
import h5pyd


def main():
    """Display CLI help instructions."""
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("usage: python get_root_attrs.py <hobo_file>")
        print("example: python get_root_attrs.py hdf5://projects/nsfarctic/uva_test.h5")
        sys.exit()
    filepath = sys.argv[1]
    f = h5pyd.File(filepath)

    for k in f.attrs:
        v = f.attrs[k]
        print(f"{k}: {v}")


#
# Main
#
main()
