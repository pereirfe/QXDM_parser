#!/usr/bin/python

import fnmatch
from subprocess import call
import sys
import os

target_dir =  "/home/fernandopereira/QXDM/txt/"
output_dir = "/home/fernandopereira/QXDM/proc/"

format_in  = ".txt"
format_out = "PARSED.txt"

op_dir  = "/home/fernandopereira/git_works/QXDM_parser/"
op_path = op_dir + "QXDM_parser.py"

for subdir, dirs, files in os.walk(target_dir, followlinks=True):
    for f in files:
        if f.endswith(format_in):
            tgtf = target_dir + f
            tgte = op_dir + "events.json"
            call(["python", op_path, tgtf, tgte])
