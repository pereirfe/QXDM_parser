#!/usr/bin/python
import sys



def main():
    input_filename = sys.argv[1]
    output_filename = input_filename + "_PARSED.txt"

    codes_search = ["0xB18B"] #ToDo: Generalize, use a JSON

    t_found = [ [] for x in codes_search ]
    intervals_found = [ [] for x in codes_search ]
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

    arg = []

    with open(input_filename, 'r') as infile, open(output_filename, 'w'):
        for line in infile:

            # ToDo: Default must register what happens inbetween intervals
            if state == "default":
                if line[0:2] != '201':             # Ignores Inside Blocks
                    continue

                for code in codes_search:
                    if code in line:
                        state = "code_found"
                        current_code = code

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
