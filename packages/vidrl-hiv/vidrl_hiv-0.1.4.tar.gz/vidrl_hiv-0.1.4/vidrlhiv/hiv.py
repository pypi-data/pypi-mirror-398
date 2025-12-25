import argparse
from importlib.resources import files, as_file
import os
import subprocess
import sys
import re
import itertools
import csv

def check_fastq(filename):
    fastq_name = filename.split("/")[-1]
    count_d = fastq_name.count("_")
    if count_d > 2:
        print(f"please check your fastq filename : {fastq_name}, there are more than 2 _ in the filename which will mislead Micall")
        return False
    return True

def input_check(samplesheet):
    ## check whether this is duplicate sample ID
    ## check whether the fastq files were named legally
    print("... Checking the input samplesheet ...")
    with open(samplesheet, 'r') as myinput:
        csvreader = csv.reader(myinput)
        cols = list(next(csvreader))
        if len(cols) != 4:
            print(f"Error, the column number is {len(cols)} instead of 4, please check your input format")
            return False
        else:
            if cols[0][0] != "#":
                print(f"Error, # is requested ahead of first column name, please edit your samplesheet")
                return False
            else:
                names = []
                file_check = []
                for line in csvreader:
                    names.append(line[0])
                    file_check.append(check_fastq(line[1]))
                    file_check.append(check_fastq(line[2]))
                if len(names) != len(set(names)):
                    print("Error, there are dup sample ids in the samplesheet")
                    return False
                if False in file_check:
                    print("Error, please check the fastq names")
                    return False
                print("... Samplesheet Checking is Done ...")
                return True


def bash_command(cmd):
	p = subprocess.Popen(cmd, shell=True)
	while True:
		return_code = p.poll()
		if return_code is not None:
			break
	return

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
                new_rows.append(["#sample"] + row[1:3] + ["reference"])
                count +=1
            else:
                new_rows.append(row + ["hxb2"])
    with open(csvpath, 'w', newline="") as myout:
        csvwriter = csv.writer(myout)
        for row in new_rows:
            csvwriter.writerow(row)
    return csvpath

def run_snakemake(snakefile, configfile, samplesheet, inputfolder, njob, ncode):
    command_line = f'snakemake -c {ncode} -j {njob} -s {snakefile} --config sample_sheet="{samplesheet}" input_folder="{inputfolder}" --configfile {configfile} --use-conda'
    print("Start to run snakemake")
    print(command_line)
    bash_command(command_line)

def run_dirty_pipeline(snakefile, samplesheet, outputfolder, workfolder, njob, ncode):
    command_line = f'snakemake -c {ncode} -j {njob} -s {snakefile} --config samplesheet="{samplesheet}" outputfolder="{outputfolder}" -d {workfolder} --use-conda'
    print("Start to run dirty_pipeline")
    print(command_line)
    bash_command(command_line)

def run_R_command(Rscript, bed, pdf, depthf=""):
    if len(str(depthf)) == 0:
        command_line = f"Rscript {Rscript} -i {bed} -o {pdf}"
    else:
        command_line = f"Rscript {Rscript} -i {bed} -o {pdf} -d {depthf}"
    print("Running R-plot scripts to generate the plot")
    print(command_line)
    bash_command(command_line)

def reformat_dirtysamplesheet(path_to_file):
    new_rows = []
    with open(path_to_file, 'r') as mydirty:
        csvreader = csv.reader(mydirty)
        title = next(csvreader)
        new_rows.append(title)
        for line in csvreader:
            cwd = os.getcwd()
            r1 = str(os.path.abspath(line[1]))
            r2 = str(os.path.abspath(line[1]))
            new_rows.append([line[0], r1, r2, line[3]])
    with open(os.path.join(os.getcwd(), "dirtyinput.csv"), 'w', newline="") as myout:
        csvwriter = csv.writer(myout)
        for row in new_rows:
            csvwriter.writerow(row)
    return os.path.join(os.getcwd(), "dirtyinput.csv")

def main():
    parser=argparse.ArgumentParser(description="Runing VIDRL HIV pipeline")
    parser.add_argument("samplesheet", help="input a samplesheet to run VIDRL HIV analysis")
    #parser.add_argument("--dirtyinput", help="input samplesheet for dirty pipeline to run")
    parser.add_argument("--cpu", default=10, help="Number of CPU")
    parser.add_argument("--maxjob", default=10, help="Max number of job to run together")
    parser.add_argument("--micallonly", action='store_true', help="Run Micall only")
    parser.add_argument("--dirtyonly", action="store_true", help="Run dirtypipeline only")
    args = parser.parse_args()
    abs_path = ""
    try:
        abs_path = os.path.abspath(args.samplesheet)
    except:
        print(f"Error, {args.samplesheet} is invalid, please check your input")
        sys.exit()
    samplesheet = "NA"
    inputfolder = "NA"
    dirtysamplesheet = ""
    if os.path.isdir(abs_path):
        inputfolder = abs_path
        # if args.dirtyinput:
        #     dirtysamplesheet = os.path.abspath(args.dirtyinput)
        dirtysamplesheet = os.path.abspath(filetosamplesheet(inputfolder, "./dirtysamplesheet.csv"))
    else:
        samplesheet = abs_path
        #dirtysamplesheet = os.path.abspath(samplesheetaddref(samplesheet, "./dirtysamplesheet.csv"))
        dirtysamplesheet = reformat_dirtysamplesheet(abs_path)
    
    #add samplesheet check to avoid some miss input situation
    if not input_check(samplesheet):
        sys.exit()

    #find snakefile and configfile in resources
    snakefile = ""
    configfile = ""
    package_root = files("vidrlhiv")
    snakefile = package_root/'resources'/'Snakefile'
    configfile = package_root/'resources'/'config.yaml'
    if args.dirtyonly:
        print("[LOG] skipping micall due to parameter --dirtyonly")
    else:
        run_snakemake(snakefile, configfile, samplesheet, inputfolder, args.maxjob, args.cpu)

    #running dirty pipeline
    snakefile2 = package_root/'dirty_pipeline_ammar'/'snakefile'
    cwfolder = os.getcwd()
    output_path = os.path.join(cwfolder, "dirtypipeline/results")

    if args.micallonly:
        print("[LOG] skipping dirtypipeline due to parameter --micallonly")
    else:
        run_dirty_pipeline(snakefile2, dirtysamplesheet, str(output_path), "./dirtypipeline", args.maxjob, args.cpu)

        #running R script to generate plots
        gene_plot_script = package_root/'dirty_pipeline_ammar'/'scripts'/'plot_mosdepth_genes.R'
        drm_plot_script = package_root/'dirty_pipeline_ammar'/'scripts'/'plot_mosdepth_drm.R'
        gene_bed_path = os.path.join(output_path, "all.gene.bed")
        drm_bed_path = os.path.join(output_path, "all.drm.bed")
        gene_pdf = os.path.join(output_path,"gene.pdf")
        drm_pdf = os.path.join(output_path, "drm.pdf")
        depth_csv = package_root/'dirty_pipeline_ammar'/'resources'/'depth.totals.csv'
        run_R_command(gene_plot_script, gene_bed_path, gene_pdf)
        run_R_command(drm_plot_script, drm_bed_path, drm_pdf, depth_csv)




if __name__ == "__main__":
    main()

