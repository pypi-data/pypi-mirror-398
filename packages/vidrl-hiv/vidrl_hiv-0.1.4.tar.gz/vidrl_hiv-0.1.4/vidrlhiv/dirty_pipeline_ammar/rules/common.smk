import sys
import os
import pandas as pd
from  pathlib import Path
from collections import defaultdict
from importlib.resources import files, as_file

# From the amazing https://github.com/gbouras13/hybracter
def samplesFromCsv(csvFile):
    """
    Read samples and files from a CSV
    4 cols:
        1 = sampleid
        2 = R1 Short
        3 = R2 Short
        4 = runtype

    """
    outDict = {}
    with open(csvFile, "r", encoding="utf-8") as csv:
        for line in csv:
            l = line.strip().split(",")
            if l[0].startswith("#"):
                continue
            if len(l) == 4:
                outDict[l[0]] = {}
                if (
                    #type(l[1]) is str
                    isinstance(l[3], str)
                    and os.path.isfile(l[1])
                    and os.path.isfile(l[2])
                ):
                    outDict[l[0]]["R1"] = l[1]
                    outDict[l[0]]["R2"] = l[2]
                    outDict[l[0]]["reference"] = l[3]
                else:
                    sys.stderr.write(
                        "\n"
                        f"    Error parsing {csvFile}.\n"
                        f"    {l[1]} must be paired-end or single-end or long or \n"
                        f"    {l[2]} must exist or \n"
                        f"    {l[3]} must exist or \n"
                        "    Check formatting, and that \n"
                        "    file names and file paths are correct.\n"
                        "\n"
                    )
                    sys.exit(1)
            else:
                sys.stderr.write(
                    "\n"
                    f"    FATAL: Error parsing {csvFile}. Line {l} \n"
                    f"    does not have 4 columns. \n"
                    f"    Please check the formatting of {csvFile}. \n"
                )
                sys.exit(1)
    return outDict


def parseSamples(csvfile):
    """
    From the amazing https://github.com/gbouras13/hybracter
    """
    if os.path.isfile(csvfile):
        sampleDict = samplesFromCsv(csvfile)
    else:
        sys.stderr.write(
            "\n"
            f"    FATAL: something is wrong. Likely {csvfile} is neither a file nor directory.\n"
            "\n"
        )
        sys.exit(1)

    # checks for dupes
    SAMPLES = list(sampleDict.keys())

    # Check for duplicates
    has_duplicates = len(SAMPLES) != len(set(SAMPLES))

    # error out if dupes
    if has_duplicates is True:
        sys.stderr.write(
            f"Duplicates found in the SAMPLES list in column 1 of {csvfile}.\n"
            f"Please check {csvfile} and give each sample a unique name!"
        )
        sys.exit(1)

    return sampleDict

# get inputs
def get_input_r1(wildcards):
    return DICTREADS[wildcards.sample]["R1"]

def get_input_r2(wildcards):
    return DICTREADS[wildcards.sample]["R2"]

def get_ref_fasta(wildcards):
    refname = DICTREADS[wildcards.sample]['reference']
    package_root = files("vidrlhiv")
    ref_path = package_root/'dirty_pipeline_ammar'/'resources'/'references'
    return(f"{ref_path}/{refname}.fasta")

def get_ref_path(wildcards):
    refname = DICTREADS[wildcards.sample]['reference']
    package_root = files("vidrlhiv")
    ref_path = package_root/'dirty_pipeline_ammar'/'resources'/'references'
    return(f"{ref_path}/{refname}")

##### Messesges #####
onsuccess:
    print("\n")
    print("\033[1m\033[92mSuccess! Check assembles/ folder for results.\033[0m")

onerror:
    print("\n")
    print("\033[1m\033[96m Error detected. PLEASE READ THE ERROR then check output folder first\033[0m")