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

def wc(filename):
    return int(check_output(["wc", "-l", filename]).split()[0])

def progressing(filename):
    total = wc(filename)

    print "Progression: ",

    while linenum < total:
        psize = int(math.floor(100*float(linenum)/float(total))/2)

        sys.stdout.write('█' * psize)
        sys.stdout.write(' ' * (50-psize))
        sys.stdout.write('| ')
        if psize*2 < 10:
            sys.stdout.write(' ')
            sys.stdout.write(str(psize*2))
            sys.stdout.write('%')
        else:
            sys.stdout.write(str(psize*2))
            sys.stdout.write('%')

        time.sleep(2)
        sys.stdout.write('\b'*55),

    sys.stdout.write('██████████████████████████████████████████████████| 100%\n')


def main():

    global linenum
    line_offset = 5000
    enable_progress = False

    input_filename = sys.argv[1]
    spec_filename  = sys.argv[2]
    output_filename = input_filename + "_PARSED"

    spec = json.load(open(spec_filename, 'r'))
    codes_search = spec["codes_search"]
    codes_markers = spec["codes_markers"]
    frame_markers = spec["frame_markers"]
    sframe_markers = spec["sframe_markers"]

    intervals_found = [ [] for x in codes_search ]
    events_found = [ [] for x in codes_search ]

    state = "offset"

    substage = 0
    candidate_code = 0
    time_compiled = 0
    time_compilation_steps = 0
    block_finished = 0

    arg = []

    code_extractor  = re.compile('0x[A-Fa-f0-9][A-Fa-f0-9][A-Fa-f0-9][A-Fa-f0-9]')
    value_extractor = re.compile('\d+')
    block_matcher   = re.compile('\d\d\d\d [A-Za-z][A-Za-z][A-Za-z]')

    if enable_progress:
        progression_thread = threading.Thread(target=progressing, args=(input_filename,))
        progression_thread.start()

    print "Loading", input_filename, "..."
    with open(input_filename, 'r') as infile, open(output_filename, 'w') as outfile:
        for line in infile:
            linenum += 1
            if state == "offset":
                if linenum > line_offset:
                    state = "default"
                    print "Loaded!"
                else:
                    continue

            if state == "default":
                if block_matcher.match(line):       # New block
                    candidate_code = (code_extractor.findall(line))[0]
                    block_finished = 0
                    for code in codes_search:
                        if code == candidate_code:
                            state = "code_found"
                            current_code = candidate_code

                else:                               # Inside a non-searched Block
                    if not block_finished:              # Used to block processing after getting info
                        for fm in frame_markers:            # Detect if line is a frame
                            try:
                                if fm in line:
                                    time_compilation_steps += 1
                                    time_compiled += 10*int(value_extractor.findall(line)[-1])
                            except:
                                pass

                        for sfm in sframe_markers:          # Detect if line is a subframe
                            try:
                                if sfm in line:
                                    time_compilation_steps += 1
                                    time_compiled += 1*int(value_extractor.findall(line)[-1])
                            except:
                                pass

                        if time_compilation_steps == 2:                 # when both frame and subframe were found
                            for cd_idx in range(len(codes_search)):
                                for i in range(len(intervals_found[cd_idx])):  # ToDo: Fix. Not considering multiple codes
                                    intv = intervals_found[cd_idx][i]
                                    # print intv, i, len(intervals_found), intervals_found
                                    if intv[0] <= time_compiled and intv[1] >= time_compiled:
                                        events_found[cd_idx].append(candidate_code)

                            candidate_code = 0
                            block_finished = 1
                            time_compilation_steps = 0
                            time_compiled = 0

            if state == "code_found":
                if codes_markers[current_code][substage] in line:
                    arg.append(int(value_extractor.findall(line)[-1]))
                    # print "CODE FOUND: ", current_code, "\nVALUE: ", int(value_extractor.findall(line)[-1]), "\nLINENUM:", linenum
                    # raw_input("FOUND")
                    substage += 1

                    if substage == len(codes_markers[current_code])-1: #last one which is not an instruction
                        v = [0, 0]

                        for i in range(len(codes_markers[current_code][-1][0])):
                            v[0] += codes_markers[current_code][-1][0][i]*arg[i]

                        for i in range(len(codes_markers[current_code][-1][1])):
                            v[1] += codes_markers[current_code][-1][1][i]*arg[i]

                        arg = []
                        substage = 0

                        intervals_found[codes_search.index(current_code)].append(v)      # Interval Created
                        state = "default"

        print >> outfile, "Intervals Found: "
        pprint(intervals_found, stream=outfile)
        print >> outfile, "Events Found: "
        pprint(events_found, stream=outfile)

if __name__ == "__main__":
    main()
