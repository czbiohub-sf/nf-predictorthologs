#! /usr/bin/env python3
"""
Given a signature file and a collection of sequences, output all of the
k-mers and sequences that match a hashval in the signature file.

Cribbed from https://github.com/dib-lab/sourmash/pull/724/
"""
import sys
import argparse
import sourmash
from sourmash import MinHash
from sourmash import sourmash_args
from sourmash._minhash import hash_murmur
import screed
import csv
from sourmash.logging import notify, error
from sourmash.cli.utils import add_construct_moltype_args, add_ksize_arg
from sourmash.sourmash_args import calculate_moltype
from sencha.sequence_encodings import encode_peptide, AMINO_ACID_SINGLE_LETTERS


NOTIFY_EVERY_BP = 1e7


def main():
    p = argparse.ArgumentParser()
    p.add_argument("query")  # signature file
    p.add_argument(
        "--output-hashes", type=str, default=None, help="save hashes to this file.",
    )

    args = p.parse_args()

    # first, load the signature and extract the hashvals
    sigobj = sourmash.load_one_signature(args.query)

    hashes = [str(x) + "\n" for x in sigobj.minhash.get_hashes()]
    with open(args.output_hashes, "wt") as f:
        f.writelines(hashes)

    n = len(hashes)
    notify("wrote {} n hashes to file", n)


if __name__ == "__main__":
    sys.exit(main())
