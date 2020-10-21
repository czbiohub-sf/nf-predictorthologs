#! /usr/bin/env python3
"""
Given a list of hash values and a collection of sequences, output
all of the k-mers that match a hashval.
NOTE: for now, only implemented for DNA & for seed=42.
"""
import argparse
import csv
import os
import sys

import screed
from sencha.sequence_encodings import encode_peptide, AMINO_ACID_SINGLE_LETTERS
from sourmash._minhash import hash_murmur
from sourmash.logging import notify, error
from sourmash.cli.utils import add_construct_moltype_args, add_ksize_arg
from sourmash.sourmash_args import calculate_moltype

NOTIFY_EVERY_BP = 1e7


def get_kmer_moltype(sequence, start, ksize, moltype, input_is_protein):
    kmer_in_seq = sequence[start : start + ksize]
    if moltype == "DNA":
        # Get reverse complement
        kmer_rc = screed.rc(kmer)
        if kmer_in_seq > kmer_rc:  # choose fwd or rc
            kmer_encoded = kmer_rc
        else:
            kmer_encoded = kmer_in_seq
    elif input_is_protein:
        kmer_encoded = encode_peptide(kmer_in_seq, moltype)
    elif not input_is_protein:
        raise NotImplementedError(
            "Currently cannot translate DNA to protein sequence"
        )
    return kmer_encoded, kmer_in_seq


def revise_ksize(ksize, moltype, input_is_protein):
    """If input is protein, then divide the ksize by three"""
    if moltype == "DNA":
        return ksize
    elif input_is_protein:
        # Ksize includes codons
        return int(ksize / 3)
    else:
        return ksize


def get_kmers_for_hashvals(sequence, hashvals, ksize, moltype, input_is_protein):
    "Return k-mers from 'sequence' that yield hashes in 'hashvals'."
    # uppercase!
    sequence = sequence.upper()

    # Divide ksize by 3 if sequence is protein
    ksize = revise_ksize(ksize, moltype, input_is_protein)

    for start in range(0, len(sequence) - ksize + 1):
        # Skip protein sequences with invalid input
        # (workaround for sencha bug that wrote "Writing translate
        # summary to coding_summary.json" to standard output and thus to the
        # protein fasta)
        if input_is_protein:
            if not all(x in AMINO_ACID_SINGLE_LETTERS for x in sequence):
                continue

        kmer_encoded, kmer_in_seq = get_kmer_moltype(sequence, start, ksize, moltype, input_is_protein)

        # NOTE: we do not avoid non-ACGT characters, because those k-mers,
        # when hashed, shouldn't match anything that sourmash outputs.
        hashval = hash_murmur(kmer_encoded)
        if hashval in hashvals:
            yield kmer_encoded, kmer_in_seq, hashval


def maybe_traverse_directory(seqfiles):
    for filename in seqfiles:
        if os.path.isfile(filename):
            yield filename
        else:
            for (dirpath, dirnames, basenames) in os.walk(filename):
                for basename in basenames:
                    if not basename.startswith('.'):
                        yield  os.path.join(dirpath, basename)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("hashfile")  # file that contains hashes
    p.add_argument(
        "seqfiles", nargs="+"
    )  # sequence files from which to look for matches
    p.add_argument(
        "--output-sequences",
        type=str,
        default=None,
        help="save matching sequences to this file.",
    )
    p.add_argument(
        "--output-kmers",
        type=str,
        default=None,
        help="save matching kmers to this file.",
    )
    p.add_argument(
        "--input-is-protein",
        action="store_true",
        help="Consume protein sequences - no translation needed.",
    )
    p.add_argument(
        "--first",
        action="store_true",
        help="Return only the first instance of the found k-mer(s) and "
        "sequence from each provided sequence file. Useful if you are "
        "searching for only one k-mer",
    )
    add_ksize_arg(p)
    add_construct_moltype_args(p)
    args = p.parse_args()

    # set up the outputs.
    seqout_fp = None
    if args.output_sequences:
        seqout_fp = open(args.output_sequences, "wt")

    kmerout_fp = None

    if not (seqout_fp or kmerout_fp):
        error("No output options given!")
        return -1

    if args.output_kmers:
        kmerout_fp = open(args.output_kmers, "wt")
        kmerout_w = csv.writer(kmerout_fp)
        kmerout_w.writerow(["kmer_in_sequence", "kmer_in_alphabet", "hashval", "read_name"])

    # Ensure that protein ksizes are divisible by 3
    if (args.protein or args.dayhoff or args.hp) and not args.input_is_protein:
        if args.ksize % 3 != 0:
            error("protein ksizes must be divisible by 3, sorry!")
            error("bad ksizes: {}", ", ".join(args.ksize))
            sys.exit(-1)

    # load in all the hashes
    hashes = set()
    for line in open(args.hashfile, "rt"):
        line = line.strip()
        # Skip empty lines
        if line:
            try:
                hashval = int(line)
            except ValueError:
                # Assume this is a csv and the first item is the hashval
                hashval = int(line.split(',')[0])
            hashes.add(hashval)

    moltype = calculate_moltype(args)

    if not hashes:
        error("ERROR, no hashes loaded from {}!", args.hashfile)
        return -1

    notify("loaded {} distinct hashes from {}", len(hashes), args.hashfile)

    # now, iterate over the input sequences and output those that overlap
    # with hashes!
    n_seq = 0
    n = 0  # bp loaded
    m = 0  # bp in found sequences
    p = 0  # number of k-mers found
    found_kmers = []
    watermark = NOTIFY_EVERY_BP
    for filename in maybe_traverse_directory(args.seqfiles):
        try: 
            m, n = get_matching_hashes_in_file(
                filename,
                args.ksize,
                moltype,
                args.input_is_protein,
                hashes,
                found_kmers,
                m,
                n,
                n_seq,
                seqout_fp,
                watermark,
                args.first,
            )
            if args.first and m > 0:
                break
        except ValueError:
            notify(f"Unable to read {filename} as a fasta file, skipping")

    if seqout_fp:
        notify("read {} bp, wrote {} bp in matching sequences", n, m)

    if kmerout_fp and found_kmers:
        for kmer_in_seq, kmer_encoded, hashval, read_id in found_kmers:
            kmerout_w.writerow([kmer_in_seq, kmer_encoded, str(hashval), read_id])
        notify("read {} bp, found {} kmers matching hashvals", n, len(found_kmers))


def get_matching_hashes_in_file(
    filename,
    ksize,
    moltype,
    input_is_protein,
    hashes,
    found_kmers,
    m,
    n,
    n_seq,
    seqout_fp,
    watermark,
    first=False,
):
    for record in screed.open(filename):
        n += len(record.sequence)
        n_seq += 1
        while n >= watermark:
            sys.stderr.write("... {} {} {}\r".format(n_seq, watermark, filename))
            watermark += NOTIFY_EVERY_BP

        # now do the hard work of finding the matching k-mers!
        for kmer_encoded, kmer_in_seq, hashval in get_kmers_for_hashvals(
            record.sequence, hashes, ksize, moltype, input_is_protein
        ):
            found_kmers.append([kmer_in_seq, kmer_encoded, hashval, record['name']])

            # write out sequence
            if seqout_fp:
                seqout_fp.write(">{}|hashval:{}|kmer:{}|kmer_encoded:{}\n{}\n".format(
                    record.name, hashval, kmer_in_seq, kmer_encoded, record.sequence))
                m += len(record.sequence)
            if first:
                return m, n
    return m, n


if __name__ == "__main__":
    sys.exit(main())
