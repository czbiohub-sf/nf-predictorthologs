#!/usr/bin/env python

import os
import argparse
import pybedtools


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-bam", help="bam file to subset")
    parser.add_argument("-bed", help="bed file with index info")

    args = parser.parse_args()

    prefix, ext = os.path.splitext(os.path.basename(args.bam))
    
    bed = pybedtools.BedTool(args.bed)
    bam = pybedtools.BedTool(args.bam)

    for subset in bam.intersect(bed):
        with open(f"{prefix}_{subset.start}_{subset.end}.fastq", "w") as fh:
            fh.write(f"{subset.fields[0]}\n") # sequencer ID
            fh.write(f"{subset.fields[9]}\n") # sequence
            fh.write("+\n")
            fh.write(f"{subset.fields[10]}") # read score

