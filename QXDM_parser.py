#!/usr/bin/python
import sys
import re
import threading
import time
from subprocess import check_output
import math

linenum = 0

def wc(filename):
    return int(check_output(["wc", "-l", filename]).split()[0])

def progressing(filename):
    total = wc(filename)

    print "Progression: ",

    while linenum < total:
        psize = math.floor(100*float(linenum)/float(total))

        print '█' * psize,
        print ' ' * (100-psize),
        print '| ', psize, "%",

        time.sleep(5)
        print '\b'*105





def main():
    input_filename = sys.argv[1]
    output_filename = input_filename + "_PARSED.txt"

    codes_search = ["0xB18B"] #ToDo: Generalize, use a JSON

    t_found = [ [] for x in codes_search ]
    intervals_found = [ [] for x in codes_search ]
    events_found = [ [] for x in codes_search ]

    codes_markers = { codes_search[0]:[ "Sleep Subframe",
                                        "Sleep SFN",
                                        "Wakeup SFN",
                                        "Wakeup Subframe",
                                        [[1,10,0,0],[0,0,10,1]]
                                      ]
                    }

    frame_markers  = [ "System FN",
                       "System Frame Number",
                       "Current SFN"
                     ]

    sframe_markers = [ "Sub-frame Number",
                       "Sub Frame Number",
                       "Current Subframe Number"
                     ]

    state = "default"

    current_code = 0
    substage = 0
    candidate_code = 0
    time_compiled = 0
    time_compilation_steps = 0
    block_finished = 0

    arg = []

    code_extractor  = re.compile('0x[A-Fa-f0-9][A-Fa-f0-9][A-Fa-f0-9][A-Fa-f0-9]')
    value_extractor = re.compile('\d+')

    progression_thread = threading.Thread(target=progressing, args=(filename))
    progression_thread.start()

    with open(input_filename, 'r') as infile, open(output_filename, 'w'):
        for line in infile:
            linenum += 1

            if state == "default":
                if line[0:2] != '201':              # New block
                    candidate_code = (code_extractor.findall(line))[0]
                    block_finished = 0
                    for code in codes_search:
                        if code == candidate_code:
                            state = "code_found"

                else:                               # Inside a non-searched Block
                    if not block_finished:              # Used to block processing after getting info
                        for fm in frame_markers:            # Detect if line is a frame
                            if fm in line:
                                time_compilation_steps += 1
                                time_compiled += 10*value_extractor.findall(line)[-1]

                        for sfm in sframe_markers:          # Detect if line is a subframe
                            if sfm in line:
                                time_compilation_steps += 1
                                time_compiled += 1*value_extractor.findall(line)[-1]

                        if time_compilation_steps == 2:                 # when both frame and subframe were found
                            for i in range(intervals_found):
                                intv = intervals_found[i]
                                if intv[0] <= time_compiled and intv[1] >= time_compiled:
                                    events_found[i].append(candidate_code)
                                    candidate_code = 0

                            block_finished = 1
                            time_compilation_steps = 0
                            time_compiled = 0

            if state == "code_found":
                if codes_markers[current_code][substage] in line:
                    arg.append(int(filter(str.isdigit, line)))
                    substage += 1

                    if substage == len(codes_markers[current_code])-1: #last one which is not an instruction
                        substage = 0
                        v = []
                        for i in range(len(codes_markers[current_code][-1])):           # Number of outputs
                            for j in range(len(codes_markers[current_code][-1][0])      # For each output, iterate over multipliers
                                v[i] = codes_markers[current_code][-1][i][j]*arg[j]

                        intervals_found.append(v)                                       # Interval Created
                        state = "default"
                        #Todo: How to handle this generically?

                if line[0] == '201':             # Detect the end of an Inside Block
                    state = "default"
                    continue

if __name__ == "__main__":
    main()
