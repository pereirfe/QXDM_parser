#!/usr/bin/python
# -*- coding: latin-1 -*-
import sys
import re
import threading
import time
import json
from ast import literal_eval
from subprocess import check_output

def main():

    global linenum
    line_offset = 5000
    enable_progress = True

    big_filename = sys.argv[1]
    small_filename  = sys.argv[2]
    reference_filename = sys.argv[3]

    output_filename = "report"
    
    small404 = []
    small404f = []
    big404 = []
    big404f = []

    value_extractor = re.compile('\d+')
    code_extractor  = re.compile('0x[A-Fa-f0-9][A-Fa-f0-9][A-Fa-f0-9][A-Fa-f0-9]')

    bigf = []
    big = []
    with open(big_filename, 'r') as f:
        for line in f:
            big.append(code_extractor.findall(line)[0])
            bigf.append(value_extractor.findall(line)[0])

    smallf = []
    small = []
    with open(small_filename, 'r') as f:
        for line in f:
            small.append(code_extractor.findall(line)[0])
            smallf.append(value_extractor.findall(line)[0])

    ref = []
    with open(reference_filename, 'r') as f:
        for line in f:
            ref.append(code_extractor.findall(line)[0])

    for code, f in zip(big, bigf):
        if code not in ref:
            big404.append(code)
            big404f.append(f)

    for code, f in zip(small, smallf):
        if code not in ref:
            small404.append(code)
            small404f.append(f)

    with open(output_filename, 'w') as o:
        print >>o, "Codes in BIG which are absent in reference"
        for code, f in zip(big404, big404f):
            print >>o, f, "\t", code

        print >>o, "-"*72

        print >>o, "Codes in SMALL which are absent in reference"
        for code, f in zip(small404, small404f):
            print >>o, f, "\t", code


if __name__ == "__main__":
    main()
