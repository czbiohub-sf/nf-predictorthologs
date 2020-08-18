#! /usr/bin/env python3
"""
Given a list of hash values and a collection of sequences, output
all of the k-mers that match a hashval.
NOTE: for now, only implemented for DNA & for seed=42.
"""
import sys
import argparse
import screed
import csv
import sourmash
from sourmash.logging import notify, error
from sourmash.minhash import hash_murmur
from sourmash import MinHash
from sourmash.cli.utils import add_construct_moltype_args, add_ksize_arg
from sourmash import sourmash_args
from sencha.sequence_encodings import encode_peptide, AMINO_ACID_SINGLE_LETTERS

NOTIFY_EVERY_BP = 1e7


def get_kmer_moltype(sequence, start, ksize, moltype, input_is_protein):
    kmer = sequence[start : start + ksize]
    if moltype == "DNA":
        # Get reverse complement
        kmer_rc = screed.rc(kmer)
        if kmer > kmer_rc:  # choose fwd or rc
            kmer = kmer_rc
    elif input_is_protein:
        kmer = encode_peptide(kmer, moltype)
    elif not input_is_protein:
        raise NotImplementedError("Currently cannot translate DNA to protein sequence")
    return kmer


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

        kmer = get_kmer_moltype(sequence, start, ksize, moltype, input_is_protein)

        # NOTE: we do not avoid non-ACGT characters, because those k-mers,
        # when hashed, shouldn't match anything that sourmash outputs.
        hashval = hash_murmur(kmer)
        if hashval in hashvals:
            yield kmer, hashval


def main():
    p = argparse.ArgumentParser()
    p.add_argument("hashfile")  # file that contains hashes
    p.add_argument("signatures", nargs="+")  # Signatures to look for matching hashes
    p.add_argument(
        "--output-sig",
        type=str,
        default=None,
        help="save matching signatures to this file.",
    )
    p.add_argument(
        "--output-hashes",
        type=str,
        default=None,
        help="save matching hashes to this file.",
    )
    p.add_argument(
        "--input-is-protein",
        action="store_true",
        help="Consume protein sequences - no translation needed.",
    )
    p.add_argument(
        "--from-file", help="a file containing a list of signatures file to compare"
    )
    p.add_argument(
        "--track-abundance",
        action="store_true",
        help="The hashfile is a csv containing the hashval,abundance on each line. "
        "Use this abundance as the abundance for each hash",
    )
    p.add_argument(
        '--traverse-directory', action='store_true',
        help='compare all signatures underneath directories'
    )
    p.add_argument(
        '-f', '--force', action='store_true',
        help='continue past errors in file loading'
    )
    p.add_argument("--scaled", default=None, type=int)

    add_ksize_arg(p)
    add_construct_moltype_args(p)
    args = p.parse_args()

    # set up the outputs.
    sigout_fp = None
    if args.output_sig:
        sigout_fp = open(args.output_sig, "wt")

    hashout_fp = None
    if args.output_sig:
        hashout_fp = open(args.output_hashes, "wt")
        hashout_w = csv.writer(hashout_fp)
        hashout_w.writerow(["hashval", "abundance"])

    if not (sigout_fp or hashout_fp):
        error("No output options given!")
        return -1

    # Ensure that protein ksizes are divisible by 3
    if (args.protein or args.dayhoff or args.hp) and not args.input_is_protein:
        if args.ksize % 3 != 0:
            error("protein ksizes must be divisible by 3, sorry!")
            error("bad ksizes: {}", ", ".join(args.ksize))
            sys.exit(-1)

    # first, load in all the hashes
    hashes = {}
    for line in open(args.hashfile, "rt"):
        if args.track_abundance:
            hashval, abundance = map(int, line.strip().split(","))
        else:
            hashval = int(line.strip())
            abundance = 1
        hashes[hashval] = abundance

    if not hashes:
        error("ERROR, no hashes loaded from {}!", args.hashfile)
        return -1

    moltype = sourmash_args.calculate_moltype(args)

    if not hashes:
        error("ERROR, no hashes loaded from {}!", args.hashfile)
        return -1

    notify("loaded {} distinct hashes from {}", len(hashes), args.hashfile)

    # Get all signature files
    inp_files = list(args.signatures)
    if args.from_file:
        more_files = sourmash_args.load_file_list_of_signatures(args.from_file)
        inp_files.extend(more_files)

    progress = sourmash_args.SignatureLoadingProgress()

    # Read and error check signature files
    # load in the various signatures
    siglist = []
    ksizes = set()
    moltypes = set()
    for filename in inp_files:
        notify("loading '{}'", filename, end="\r")
        loaded = sourmash_args.load_file_as_signatures(
            filename,
            ksize=args.ksize,
            select_moltype=moltype,
            traverse=args.traverse_directory,
            yield_all_files=args.force,
            progress=progress,
        )
        loaded = list(loaded)
        if not loaded:
            notify(
                "\nwarning: no signatures loaded at given ksize/molecule type from {}",
                filename,
            )
        siglist.extend(loaded)

        # track ksizes/moltypes
        for s in loaded:
            ksizes.add(s.minhash.ksize)
            moltypes.add(sourmash_args.get_moltype(s))

        # error out while loading if we have more than one ksize/moltype
        if len(ksizes) > 1 or len(moltypes) > 1:
            break

    # Get hashes contained in signatures
    hashes_in_sigs = set([])
    for sig in siglist:
        this_sig_hashes = set(sig.minhash.get_hashes()).intersection(hashes.keys())
        hashes_in_sigs.update(this_sig_hashes)

    # Add abundances
    if args.track_abundance:
        hashes_in_sigs = {h: hashes[h] for h in hashes_in_sigs}
    else:
        hashes_in_sigs = dict.fromkeys(hashes_in_sigs, 1)

    n_intersecting_hashes = len(hashes_in_sigs)
    notify(
        "Read {} hashes, found {} of them present in {} signatures",
        len(hashes),
        n_intersecting_hashes,
        len(siglist),
    )
    if sigout_fp:
        # now, create the MinHash object that we'll use.
        scaled = 0
        num = 0
        if args.scaled:
            scaled = args.scaled
        elif args.num:
            num = args.num
        else:
            notify("setting --num automatically from the number of hashes.")
            num = len(hashes)

        # construct empty MinHash object according to args
        minhash = MinHash(
            n=num,
            ksize=args.ksize,
            scaled=scaled,
            dayhoff=args.dayhoff,
            is_protein=args.input_is_protein,
            hp=args.hp,
            track_abundance=args.track_abundance,
        )
        # add hashes with abundances into MinHash!
        if args.track_abundance:
            minhash.set_abundances(hashes_in_sigs)
        else:
            minhash.add_many(hashes_in_sigs.keys())

        if len(minhash) < n_intersecting_hashes:
            notify(
                "WARNING: loaded {} hashes, but only {} made it into MinHash.",
                len(hashes),
                len(minhash),
            )
            if scaled:
                notify("This is probably because of the scaled argument.")
            elif args.num:
                notify("This is probably because your --num is set to {}", args.num)

        if num > len(minhash):
            notify(
                "WARNING: --num set to {}, but only {} hashes in signature.",
                num,
                len(minhash),
            )

        sigobj = sourmash.SourmashSignature(
            minhash, name=args.name, filename=args.filename
        )

        with open(args.output, "wt") as fp:
            sourmash.save_signatures([sigobj], fp)
        notify("wrote signature to {}", args.output)
        sigout_fp.close()

    if hashout_fp:
        for hashval, abundance in hashes_in_sigs.items():
            hashout_w.writerow([str(hashval), str(abundance)])
        notify("read {} bp, found {} kmers matching hashvals", n, len(found_kmers))
        hashout_fp.close()


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
        for kmer, hashval in get_kmers_for_hashvals(
            record.sequence, hashes, ksize, moltype, input_is_protein
        ):
            found_kmers[kmer] = hashval

            # write out sequence
            if seqout_fp:
                seqout_fp.write(">{}\n{}\n".format(record.name, record.sequence))
                m += len(record.sequence)
            if first:
                return m, n
    return m, n


if __name__ == "__main__":
    sys.exit(main())
