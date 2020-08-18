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

NOTIFY_EVERY_BP = 1e7


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
    p.add_argument("--name", default="", help="signature name")
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
        "--traverse-directory",
        action="store_true",
        help="compare all signatures underneath directories",
    )
    p.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="continue past errors in file loading",
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
        this_sig_hashes = set(sig.minhash.hashes).intersection(hashes.keys())
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
                len(hashes_in_sigs),
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
            minhash, name=args.name, filename=args.output_sig
        )

        with open(args.output_sig, "wt") as fp:
            sourmash.save_signatures([sigobj], fp)
        notify("wrote signature to {}", args.output_sig)
        sigout_fp.close()

    if hashout_fp:
        for hashval, abundance in hashes_in_sigs.items():
            hashout_w.writerow([str(hashval), str(abundance)])
        hashout_fp.close()


if __name__ == "__main__":
    sys.exit(main())
