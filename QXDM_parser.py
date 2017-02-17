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
    enable_progress = True

    input_filename = sys.argv[1]
    spec_filename  = sys.argv[2]
    output_filename = input_filename + "_PARSED"

    spec = json.load(open(spec_filename, 'r'))

    state = "offset"

    tl_time = []
    tl_code = []
    tl_string = []

    candidate_code = 0
    
    code_extractor  = re.compile('0x[A-Fa-f0-9][A-Fa-f0-9][A-Fa-f0-9][A-Fa-f0-9]')
    value_extractor = re.compile('\d+')
    table_string_extractor = re.compile('\|.*\|')
    block_matcher   = re.compile('\A\d\d\d\d [A-Za-z][A-Za-z][A-Za-z]')

    data_type = []
    f_regex  = []
    sf_regex = []
    size_regex = []
    time = []
    info_string = []
    code = 0
    n_of_rec = -1
    
    table_times = []
    table_strings = []

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
                    
            
            ###if state == "default":
            if block_matcher.match(line):       # New block
                
                #Dealing with finalization of previous block
                for dt, code_obj in zip(data_type, spec[code]):
                    if dt == "Data":
                        tl_time = tl_time + time
                        tl_code = tl_code + [code for i in spec[code]]
                        tl_string = tl_string + info_string
                    
                    if dt == "Table":
                        tl_time = tl_time + table_times
                        tl_code = tl_code + [code for i in range(n_of_rec)]
                        tl_string = tl_string + table_strings

                #Cleaning Variables
                
                n_of_rec = -1
                table_strings = []
                table_times = []
                time = []
                info_string = []

                #Dealing with the new block
                candidate_code = (code_extractor.findall(line))[0]
                if candidate_code in spec:
                    code = candidate_code
                    state = "block found"

                    for code_obj in spec[code]:
                        data_type.append(code_obj["Type"])
                        if data_type[-1] == "Table":
                           size_regex.append(re.compile(code_obj["F"]["Size_Indicator"]))
                        
                        f_regex.append(re.compile(code_obj["F"]["Match"]))
                        sf_regex.append(re.compile(code_obj["SF"]["Match"]))
                        time.append(0)
                        string.append("")
                        

            if state == "block found":
                for dt, f, sf, sz, tm, istr, code_obj in zip(data_type, f_regex, sf_regex, size_regex, time, info_string, spec[code]):
                    if dt == "Data":
                        if f.match(line):
                            tm += 10*value_extractor.findall(line)[code_obj["F"]["Index"]]
                            istr = code_obj["IDstr"]
                            
                        if sf.match(line):
                            tm += value_extractor.findall(line)[code_obj["SF"]["Index"]]
                            istr = code_obj["IDstr"]
                        
                        # DynStr parameter only allowed for tables
                    
                    elif dt == "Table":
                        if n_of_rec == -1: #If the table size is not yet known
                            if sz.match(line):
                                n_of_rec = value_extractor.findall(line)[-1]  # TODO: Specify in a generalistic way 
                                
                        else:  # In tables, each matched line contains frame, subframe and string
                            v = 0
                            s = ""
                            if f.match(line):
                                v += 10*value_extractor.findall(line)[code_obj["F"]["Index"]]
                            
                            if sf.match(line):
                                v += value_extractor.findall(line)[code_obj["SF"]["Index"]]
                                
                            if "DynStr" in code_obj:
                                s = table_string_extractor.findall(line)[code_obj["Index"]]
                            else:
                                s = code_obj["IDstr"]

                            table_times.append(v)
                            table_strings.append(s)

                    




        mean_duration = []
        for code_intervals, code, event_list in zip(intervals_found, codes_search, events_found):
            acc = 0
            for interval in code_intervals:
                acc += (interval[1]-interval[0])

            print >> outfile, "Searching for Intervals Between", code, "references"
            print >> outfile, "\t- No. Intervals:\t\t", len(code_intervals)
            print >> outfile, "\t- Mean Duration:\t\t", float(acc)/len(code_intervals)
            print >> outfile, "\t- No. Events Found:\t\t", len(event_list)
            print >> outfile, "\t- No. Distinct Events Found:\t", len(set(event_list))
            for uevent in set(event_list):
                print >> outfile, "\t\t-", uevent, ":\t\t", event_list.count(uevent)

            print >> outfile, "----------------------------------------------------------"


        print >> outfile, "\n\n\n\n\nBRUTE DATA"
        print >> outfile, "----------------------------------------------------------"

        print >> outfile, "Intervals Found: "
        pprint(intervals_found, stream=outfile)
        print >> outfile, "Events Found: "
        pprint(events_found, stream=outfile)

if __name__ == "__main__":
    main()
