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

    state = "offset"

    tl_time = []
    tl_code = []
    tl_string = []

    candidate_code = 0
    
    code_extractor  = re.compile('0x[A-Fa-f0-9][A-Fa-f0-9][A-Fa-f0-9][A-Fa-f0-9]')
    value_extractor = re.compile('\d+')
    table_matchline = re.compile('^\s+\|.*\d+.*\|')
    table_string_extractor = re.compile('[^\|]*[^\|\s]+[^\|]*')
    block_matcher   = re.compile('^\d\d\d\d\s[A-Z][a-z][a-z]\s\d\d')

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
    block_processing = False

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
                state = "default"

                if block_processing:
                #Dealing with finalization of previous block
                    block_processing = False
                    for dt, code_obj in zip(data_type, spec[code]):
                        if dt == "Data":
                            tl_time = tl_time + time
                            tl_code = tl_code + [code for i in spec[code]]
                            tl_string = tl_string + info_string
                            
                        if dt == "Table":
                            tl_time = tl_time + table_times
                            tl_code = tl_code + [code for i in range(len(table_times))]
                            tl_string = tl_string + table_strings
            
                #Cleaning Variables
                n_of_rec = -1
                table_strings = []
                table_times = []
                time = []
                info_string = []
                code = 0
                data_type = []
                f_regex  = []
                sf_regex = []
                size_regex = []

                #Dealing with the new block
                candidate_code = (code_extractor.findall(line))[0]
                if candidate_code in spec:

#                    if candidate_code == "0xB193":
#                        print "FOUND", candidate_code, "at line", line
#                        raw_input("Continue?")

                    code = candidate_code
                    state = "block found"
                    block_processing = True
                    
                    for code_obj in spec[code]:
                        data_type.append(code_obj["Type"])
                        if data_type[-1] == "Table":
                           size_regex.append(re.compile(code_obj["Size_Indicator"]))
                        else:
                           size_regex.append(re.compile("xxxxxxxxxxxxxxxxxx"))

                        f_regex.append(re.compile(code_obj["F"]["Match"]))
                        sf_regex.append(re.compile(code_obj["SF"]["Match"]))
                        time.append(0)
                        info_string.append("")
                        

            if state == "block found":
#                print "---------------\nBLOCK SPEC\n---------------"
#                print data_type
#                print f_regex
#                print sf_regex
#                print size_regex
#                print time
#                print info_string
#                print spec[code]
#                print "----------------------------------------"

                
                #print "LINE: ", line
                #raw_input("Continue?")

                for dt, f, sf, sz, tm, code_obj in zip(data_type, f_regex, sf_regex, size_regex, range(len(spec[code])), spec[code]):
                    if dt == "Data":
                        if f.match(line):
                           ### print "F: ", line
                            time[tm] += 10*int(value_extractor.findall(line)[code_obj["F"]["Index"]])
                            info_string[tm] = code_obj["IDstr"]
                            
                        if sf.match(line):
                            #print "SF: ", line
                            time[tm] += int(value_extractor.findall(line)[code_obj["SF"]["Index"]])
                            info_string[tm] = code_obj["IDstr"]
                        
                        # DynStr parameter only allowed for tables
                    
                    elif dt == "Table":
                        if n_of_rec == -1: #If the table size is not yet known
                            if sz.match(line):
                                n_of_rec = int(value_extractor.findall(line)[-1])  # TODO: Specify in a generalistic way 
                                
                        else:  # In tables, each matched line contains frame, subframe and string
                            v = 0
                            s = ""
                            got_line = False
                            if f.match(line):
                                #print "MATCH F"
                                got_line = True
                                v += 10*int(value_extractor.findall(line)[code_obj["F"]["Index"]])
                            
                            if sf.match(line):
                                #print "MATCH SF"
                                got_line = True
                                v += int(value_extractor.findall(line)[code_obj["SF"]["Index"]])
                                
                            if "DynStr" in code_obj:
                                if table_matchline.match(line):
                                   # print "MATCH DNS"
                                    got_line = True
                                   # print "LINE: ", line
                                   # print "INDEX: ", code_obj["Index"]
                                   # print "STR ", table_string_extractor.findall(line)
                                    s = table_string_extractor.findall(line)[code_obj["Index"]]
                            else:
                                s = code_obj["IDstr"]
                            
                            if got_line:
                                table_times.append(v)
                                table_strings.append(s)
                            
        chunks_time = []
        chunks_code = []
        chunks_str  = []
        prev_marker = 0
        print "Dimension: ", len(tl_time)
        for i in range(1,len(tl_time)):
            if i%1000 == 0:
                print "Currently at ", i
            if (tl_time[i] - tl_time[i-1]) < -1000:
                chunks_time.append(tl_time[prev_marker:(i-1)])
                chunks_code.append(tl_code[prev_marker:(i-1)])
                chunks_str.append(tl_string[prev_marker:(i-1)])
                
                prev_marker = i
                a = zip(chunks_time[-1], chunks_code[-1], chunks_str[-1])
                a.sort()
                try:
                    chunks_time[-1], chunks_code[-1], chunks_str[-1] = zip(*a)
                except:
                    chunks_time = chunks_time[0:-1]
                    chunks_code = chunks_code[0:-1]
                    chunks_str = chunks_str[0:-1]

        #print chunks_time
        #raw_input("Continue?")
        
        for t, c, s in zip(chunks_time, chunks_code, chunks_str):
            for tm, cd, st in zip(t, c, s):
                print >> outfile, "\t\t", tm, "\t\t", cd, "\t\t", st


if __name__ == "__main__":
    main()
