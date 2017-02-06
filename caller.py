#!/usr/bin/python

import fnmatch
from subprocess import call
import sys
import os

target_dir =  "/home/fpereira/QXDM/txt/"
output_dir = "/home/fpereira/QXDM/proc/"

format_in  = ".txt"
format_out = "PARSED.txt"

op_path = "/home/fpereira/working/QXDM_Parser/QXDM_parser.py"

for subdir, dirs, files in os.walk(target_dir, followlinks=True):
    for f in files:
        if f.endswith(format_in):
            tgtf = target_dir + f
            call(["python", op_path, tgtf])
