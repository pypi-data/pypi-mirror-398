#!/usr/bin/env python3
import os
import re
import itertools
import csv

def list_all_files_recursive(directory_path):
    all_files = []
    interesting_types = ["fastq","fq","fa","fasta","fna"]
    pattern = "|".join(interesting_types)
    for root, _, files in os.walk(directory_path):
        for file in files:
            if re.search(pattern, file):
                all_files.append(os.path.join(root, file))
    return all_files

def filetosamplesheet(inputfolder,csvpath):
    input_file_list = list_all_files_recursive(inputfolder)

    #sort and paired
    sorted_list = sorted(input_file_list)
    output_lines = []
    for groupID, groupItems in itertools.groupby(sorted_list, lambda x: os.path.basename(x).split("_R")[0]):
        output_lines.append([groupID] + list(groupItems) + ["hxb2"])

    #print(output_lines)
    with open(csvpath, 'w', newline="") as myout:
        swriter = csv.writer(myout)
        swriter.writerow(["#sample","r1","r2","reference"])
        for line in output_lines:
            swriter.writerow(line)

    return csvpath

def samplesheetaddref(inputcsv, csvpath):
    new_rows = []
    count = 0
    with open(inputcsv, 'r') as myinput:
        csvreader = csv.reader(myinput)
        for row in csvreader:
            if count == 0:
                new_rows.append(row + ["reference"])
                count +=1
            else:
                new_rows.append(row + ["hxb2"])
    with open(csvpath, 'w', newline="") as myout:
        csvwriter = csv.writer(myout)
        for row in new_rows:
            csv.writerow(row)
    return csvpath
 