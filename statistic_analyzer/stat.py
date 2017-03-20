#!/usr/bin/python
# -*- coding: latin-1 -*-
import sys
import re
import time
import json
import math

class MeasureDefinition:
    ''' A class which will keep the description of measures from spec '''
    started = False

    def __init__(self, spec):
        self.rstart = re.compile(spec["rstart"])
        self.pstart = int(spec["pstart"])
        self.rend = re.compile(spec["rend"])
        self.pend = int(spec["pend"])
        self.rhit = re.compile(spec["rhit"])
        self.name = spec["name"]
        self.position = spec["position"]
        self.current_measuring = []
        self.concluded_measuring = []
        

    def checkline(self, line):
        if MeasureDefinition.started == False and self.name == "STARTPOINT":
            if self.rstart.match(line):
                MeasureDefinition.started = True

        if MeasureDefinition.started == True:
            for cm in self.current_measuring:
                cm.checkline(line)

            if (self.rstart.match(line)):
                self.current_measuring.append(Measure(self,line))

    def conclude_measure(self,m):
        self.concluded_measuring.append(m)
        self.current_measuring.remove(m)

    def get_mean(self):
        acc = 0;
        for m in self.concluded_measuring:
            st = m.gethitp(self.pstart)
            ed = m.gethitp(self.pend)
            if ed < st:
                ed += 10240
            acc += (ed - st)
 
        if len(self.concluded_measuring) == 0:
            return 0.0
        return float(acc)/len(self.concluded_measuring)
    
    def get_confidence(self):
        z = 1.96 # For 95%
        if self.get_nint() == 0:
            return 0.0

        mean = self.get_mean()
        
        acc = 0
        for m in self.concluded_measuring:
            st = m.gethitp(self.pstart)
            ed = m.gethitp(self.pend)
            if ed < st:
                ed += 10240
            t = (ed - st)
            acc += (t-mean)**2
        acc /= float(self.get_nint()-1)
        acc = math.sqrt(acc)
        acc /= math.sqrt(self.get_nint())
        acc *= z

        return acc
   
    def get_nint(self):
        return len(self.concluded_measuring)


class Measure:
    value_extractor = re.compile('\d+')

    def __init__(self, definition, line):
        self.definition = definition
        self.hits = [self.gettime(line)]

    def checkline(self, line):
        if self.definition.rhit.match(line):
            self.hits.append(self.gettime(line))

        if self.definition.rend.match(line):
            self.hits.append(self.gettime(line))
            self.definition.conclude_measure(self)

    def gettime(self, s):
        return int(self.value_extractor.findall(s)[4])

    def gethitp(self, p):
        return self.hits[p]


def main():
    input_filename = sys.argv[1]
    spec_filename =  sys.argv[2]
    output_filename = input_filename + "_STAT"

    generate_csv = False
    if len(sys.argv) == 4:
        generate_csv = True
        csv_report = sys.argv[3]

    spec = json.load(open(spec_filename, 'r'))

    meas = []
    for s in spec:
        meas.append(MeasureDefinition(s))

    with open(input_filename, 'r') as infile:
        for line in infile:
            for m in meas:
                m.checkline(line)

    with open(output_filename, 'w') as o:
        for m in meas:
            if m.name == "STARTPOINT":
                continue

            print >>o, "Measure", m.name, "\n\tNo. inputs:\t", m.get_nint()
            print >>o, "\tMeantime:\t", m.get_mean()
            print >>o, "\tConfidence:\t", m.get_confidence()
            print >>o, "\n" + "-"*40

    with open(csv_report, 'a') as o:
        print >>o, input_filename, ",", 
        for m in meas:
            if m.name == "STARTPOINT":
                continue
            print >>o, m.name, ",", m.get_nint(), ",", m.get_mean(),
            print >>o, ",", m.get_confidence(), ",",
        print >>o, ""

if __name__ == "__main__":
    main()
