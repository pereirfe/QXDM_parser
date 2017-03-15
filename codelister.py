#!/usr/bin/python
# -*- coding: latin-1 -*-
import sys
import re
import threading
import time
import json
from ast import literal_eval
from subprocess import check_output
import math
from pprint import pprint

linenum = 0

def main():
    global linenum
    line_offset = 5000

    input_filename = sys.argv[1]
    output_filename = input_filename + "_CODES"

    candidate_code = 0

    code_extractor   = re.compile('0x[A-Fa-f0-9][A-Fa-f0-9][A-Fa-f0-9][A-Fa-f0-9]')
    codestr_extractor= re.compile('0x[A-Fa-f0-9][A-Fa-f0-9][A-Fa-f0-9][A-Fa-f0-9] .*')
    value_extractor  = re.compile('\d+')
    block_matcher    = re.compile('\d\d\d\d [A-Za-z][A-Za-z][A-Za-z]')
    time_extractor   = re.compile('\d\d:\d\d:\d\d.\d\d\d')

    codecount = []
    codelist = []
    codestrlist = []

    outstate = 0

    print "Loading", input_filename, "..."
    with open(input_filename, 'r') as infile, open(output_filename, 'w') as outfile:
        for line in infile:
            linenum += 1
            if linenum > line_offset and outstate == 0:
                outstate = 1
                print "Loaded!"
            elif outstate == 0:
                continue

            if block_matcher.match(line):       # New block
                candidate_code = (code_extractor.findall(line))[0]
                codestr = (codestr_extractor.findall(line))[0]

                if candidate_code in codelist:
                    codecount[codelist.index(candidate_code)] += 1
                else:
                    codecount.append(1)
                    codelist.append(candidate_code)
                    codestrlist.append(codestr)

        st_sort = [st for (ct, st) in sorted(zip(codecount, codestrlist))]
        codecount.sort()
        for ct, st in zip(codecount, st_sort):
            print >> outfile, ct, "\t", st

if __name__ == "__main__":
    main()
