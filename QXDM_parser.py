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

def timeToMilisseconds(timestring):
    ''' Converts the timestring in the format HH:MM:SS.SSS to a integer
    in milisseconds '''

    t = int(timestring[9:12])
    t += int(timestring[6:8])
    t += int(timestring[3:5])
    t += int(timestring[0:2])

    return t

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
    tl_hour = []
    tl_code = []
    tl_string = []

    candidate_code = 0
    
    code_extractor  = re.compile('0x[A-Fa-f0-9][A-Fa-f0-9][A-Fa-f0-9][A-Fa-f0-9]')
    value_extractor = re.compile('\d+')
    table_matchline = re.compile('^\s+\|[^\|]*\d+[^\|]*\|')
    table_string_extractor = re.compile('\|[^\|]+')
    block_matcher   = re.compile('^\d\d\d\d\s[A-Z][a-z][a-z]\s\d\d')
    hour_extractor  = re.compile('\d\d:\d\d:\d\d.\d\d\d')

    data_type = []
    f_regex  = []
    sf_regex = []
    size_regex = []
    time = []
    info_string = []
    code = 0
    n_of_rec = -1
    hour_log = 0
    
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
                    if data_type[-1] == "Data":
                        tl_time = tl_time + time
                        tl_hour = tl_hour + [hour_log for i in spec[code]]
                        tl_code = tl_code + [code for i in spec[code]]
                        tl_string = tl_string + info_string
                            
                    if data_type[-1] == "Table":
                        tl_time = tl_time + table_times
                        tl_code = tl_code + [code for i in range(len(table_times))]
                        tl_hour = tl_hour + [hour_log for i in range(len(table_times))]
                        tl_string = tl_string + table_strings
            
                #Cleaning Variables
                n_of_rec = -1
                table_strings = []
                table_times = []
                time = []
                info_string = []
                code = 0
                hour_log = 0
                data_type = []
                f_regex  = []
                sf_regex = []
                size_regex = []

                #Dealing with the new block
                candidate_code = (code_extractor.findall(line))[0]
                if candidate_code in spec:

                    code = candidate_code
                    hour_log = (hour_extractor.findall(line))[0]
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
                for dt, f, sf, sz, tm, code_obj in zip(data_type, f_regex, 
                                                       sf_regex, size_regex, 
                                                       range(len(spec[code])), 
                                                       spec[code]):
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
                                n_of_rec = int(value_extractor.findall(line)[-1])  
                                # TODO: Specify in a generalistic way 
                                
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
                                                            
                            if "DynStr" in code_obj and got_line == True:
                                s = code_obj["General Prefix"] 
                                if table_matchline.match(line):
                                    for dstr in code_obj["DynStr"]:
                                        s += " {" + dstr["Prefix"] + ": \"" 
                                        s += (table_string_extractor.findall(line)[dstr["Index"]].replace("|","")).strip()
                                        s += "\"}, "
                                        
                            else:
                                try:
                                    s = code_obj["IDstr"]
                                except:
                                    if got_line:
                                        print "ERROR: no IDSTR. got_line = ", got_line

                            if got_line:
                                table_times.append(v)
                                table_strings.append(s)
                            
        chunks_time = [[]]
        chunks_hour = [[]]
        chunks_code = [[]]
        chunks_str  = [[]]
        prev_marker = 0
        cct = 0

        startmodecounter = 0
        print "Dimension: ", len(tl_time)
        for i in range(1,len(tl_time)):
            startmodecounter += 1
            if i%1000 == 0:
                print "Currently at ", i
            
            if tl_time[i] > 8000 and startmodecounter < 300:
                chunks_time[cct-1].append(tl_time[i])
                chunks_hour[cct-1].append(tl_hour[i])
                chunks_code[cct-1].append(tl_code[i])
                chunks_str[cct-1].append(tl_string[i])

            elif (tl_time[i] - tl_time[i-1]) < -5000 and startmodecounter > 300:
                chunks_time.append([])
                chunks_hour.append([])
                chunks_code.append([])
                chunks_str.append([])
                cct += 1
                startmodecounter = 0
                chunks_time[cct].append(tl_time[i])
                chunks_hour[cct].append(tl_hour[i])
                chunks_code[cct].append(tl_code[i])
                chunks_str[cct].append(tl_string[i])

            else:
                chunks_time[cct].append(tl_time[i])
                chunks_hour[cct].append(tl_hour[i])
                chunks_code[cct].append(tl_code[i])
                chunks_str[cct].append(tl_string[i])

        for i in range(len(chunks_time)):
            a = zip(chunks_time[i], chunks_hour[i], chunks_code[i], chunks_str[i])
            a.sort()
            try:
                chunks_time[i], chunks_hour[i], chunks_code[i], chunks_str[i] = zip(*a)
            except:
                chunks_time = chunks_time[0:-1]
                chunks_hour = chunks_hour[0:-1]
                chunks_code = chunks_code[0:-1]
                chunks_str = chunks_str[0:-1]
        
        for t, h, c, s in zip(chunks_time, chunks_hour, chunks_code, chunks_str):
            for tm, ho, cd, st in zip(t, h, c, s):
                print >> outfile, ho, "\t\t", tm, "\t\t", cd, "\t\t", st


if __name__ == "__main__":
    main()
