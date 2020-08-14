#! /usr/bin/env python3
"""
Given a list of hash values, create a sourmash signature.

CTB: Should eventually be added to sourmash signature import/export.
CTB: recommend people use scaled=1; make default?
"""
import sys
import argparse
import sourmash
from sourmash import MinHash
from sourmash.logging import notify, error
from sourmash.cli.utils import add_construct_moltype_args


def main():
    p = argparse.ArgumentParser()
    p.add_argument("hashfile")  # file that contains hashes
    p.add_argument("-o", "--output", default=None, help="file to output signature to")
    p.add_argument("-k", "--ksize", default=None, type=int)
    p.add_argument("--scaled", default=None, type=int)
    p.add_argument("--num", default=None, type=int)
    p.add_argument("--name", default="", help="signature name")
    p.add_argument("--filename", default="", help="filename to add to signature")
    p.add_argument(
        "--input-is-protein",
        action="store_true",
        help="Consume protein sequences - no translation needed.",
    )
    p.add_argument(
        "--track-abundance",
        action="store_true",
        help="The hashfile is a csv containing the hashval,abundance on each line. "
             "Use this abundance as the abundance for each hash",
    )
    add_construct_moltype_args(p)
    args = p.parse_args()

    # check arguments.
    if args.scaled and args.num:
        error("cannot specify both --num and --scaled! exiting.")
        return -1

    if not args.ksize:
        error("must specify --ksize")
        return -1

    if not args.output:
        error("must specify --output")
        return -1

    # first, load in all the hashes
    hashes = {}
    for line in open(args.hashfile, "rt"):
        if args.track_abundance:
            hashval, abundance = map(int, line.strip().split(','))
        else:
            hashval = int(line.strip())
            abundance = 1
        hashes[hashval] = abundance

    if not hashes:
        error("ERROR, no hashes loaded from {}!", args.hashfile)
        return -1

    # Ensure that protein ksizes are divisible by 3
    if (args.protein or args.dayhoff or args.hp) and not args.input_is_protein:
        if args.ksize % 3 != 0:
            error("protein ksizes must be divisible by 3, sorry!")
            error("bad ksizes: {}", ", ".join(args.ksize))
            sys.exit(-1)

    notify("loaded {} distinct hashes from {}", len(hashes), args.hashfile)

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
        minhash.set_abundances(hashes)
    else:
        minhash.add_many(hashes.keys())

    if len(minhash) < len(hashes):
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

    sigobj = sourmash.SourmashSignature(minhash, name=args.name, filename=args.filename)

    with open(args.output, "wt") as fp:
        sourmash.save_signatures([sigobj], fp)
    notify("wrote signature to {}", args.output)


if __name__ == "__main__":
    sys.exit(main())
