#!/usr/bin/env python
from __future__ import print_function

import argparse
import glob
import logging
from collections import defaultdict
from itertools import groupby
import os

import numpy as np
import pandas as pd
from pathvalidate import sanitize_filename
import screed
from sklearn.linear_model import LogisticRegression
from sourmash.cli.utils import add_construct_moltype_args
from sourmash.sourmash_args import calculate_moltype
from tqdm import tqdm

# Local file
import sourmash_utils

MAX_GROUP_SIZE = 100
GROUP = 'group'
SIG = 'sig'
FASTA = 'fasta'


# Default backend for scikit-learn logistic regression
PENALTY = 'l1'
SOLVER = 'saga'


# Create a logger
logging.basicConfig(format='%(name)s - %(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)


def make_hash_df(sigs, with_abundance=False):
    if with_abundance:
        records = {x.name(): x.minhash.get_mins(with_abundance=with_abundance)
                   for x in sigs}
    else:
        # Set value of each hash abundance to 1
        records = {x.name(): dict.fromkeys(x.minhash.get_mins(with_abundance=with_abundance), 1)
                   for x in sigs}
    return pd.DataFrame(records)


def make_target_vector(n_group1, n_group2):
    """Create binary target vector"""
    y_target = np.concatenate([np.ones(n_group1), np.zeros(n_group2)])
    return y_target


def get_training_data(sigs1, sigs2, with_abundance=False, verbose=False):
    """Create X feature matrix and y target vector for machine learning"""

    # Create pandas dataframe of hash abundances
    hash_df1 = make_hash_df(sigs1, with_abundance=with_abundance)
    logger.info(f"Group1 hash dataframe head: {hash_df1.head()}")

    hash_df2 = make_hash_df(sigs2, with_abundance=with_abundance)
    logger.info(f"Group2 hash dataframe head: {hash_df2.head()}")

    logger.info(f'Number of hashes in group1: {len(hash_df1.index)}')
    logger.info(f'Number of hashes in group2: {len(hash_df2.index)}')

    # Concatenate to make feature matrix
    hash_df = pd.concat([hash_df1, hash_df2], axis=1)
    X = hash_df.T
    X = X.fillna(0)

    # Create target vector "group1" is 1s and everything else is 0
    y_target = make_target_vector(len(sigs1), len(sigs2))

    return X, y_target


def differential_hash_expression(sigs1, sigs2, with_abundance=False, verbose=False,
                                 penalty=PENALTY, solver=SOLVER,
                                 random_state=0, class_weight='balanced',
                                 # Smaller C for stronger regularization
                                 # (fewer final features to look at) --> only the good stuff is left
                                 # This also (seems to) help with convergence?
                                 C=0.1,
                                 **kwargs):
    if verbose:
        print("Creating training data")
    X, y = get_training_data(sigs1, sigs2, with_abundance=with_abundance,
                             verbose=verbose)

    regressor = LogisticRegression(solver=solver, penalty=penalty, verbose=verbose,
                                   random_state=random_state, class_weight=class_weight,
                                   C=C, **kwargs)
    logger.info(f"Running logistic regression: {regressor}")
    regressor.fit(X, y)

    coefficients = pd.Series(regressor.coef_[0], index=X.columns)
    n_positive = (coefficients > regressor.tol).sum()
    logger.info(f'Number of coefficients greater than tolerance '
                f'(tolerance: {regressor.tol}): {n_positive}')

    return coefficients


def maybe_subsample(sigs, subsample_groups=MAX_GROUP_SIZE, random_state=0):
    """If number of signatures is larger than specified, subsample to random"""
    if subsample_groups is not None:
        if len(sigs) > subsample_groups:
            sigs = sigs.sample(subsample_groups, random_state=random_state)
    return sigs


def get_hashes_enriched_in_group(group1_name, annotations, group_col, sketch_series,
                                 max_group_size=MAX_GROUP_SIZE, random_state=0,
                                 verbose=False, with_abundance=False, **kwargs):
    rows = annotations[group_col] == group1_name

    group1_samples = annotations.loc[rows].index.intersection(sketch_series.index)
    logger.info(f"\nNumber of samples in {group1}: {len(group1_samples)}")

    # Everything not in group 1
    group2_samples = annotations.loc[~rows].index.intersection(sketch_series.index)
    logger.info(f"\nNumber of samples in the rest {group1}: {len(group1_samples)}")

    group1_sigs = maybe_subsample(sketch_series[group1_samples], max_group_size)
    group2_sigs = maybe_subsample(sketch_series[group2_samples], max_group_size)
    logger.info(f'\nGroup 1 signatures: {group1_sigs}')
    logger.info(f'\nGroup 2 signatures: {group2_sigs}')

    coefficients = differential_hash_expression(group1_sigs, group2_sigs,
                                                verbose=verbose,
                                                random_state=random_state,
                                                with_abundance=with_abundance,
                                                **kwargs)
    coefficients.name = group1_name
    return coefficients


def main(metadata_csv, ksize, molecule, group_col=GROUP, group1=None, sig_col=SIG,
         threshold=0, verbose=True, C=0.1, solver=SOLVER, penalty=PENALTY, n_jobs=8,
         random_state=0, use_sig_basename=False, with_abundance=False,
          max_group_size=MAX_GROUP_SIZE):
    metadata = pd.read_csv(metadata_csv, index_col='sample_id')

    if use_sig_basename:
        metadata[sig_col] = metadata[sig_col].map(os.path.basename)
    logger.info(f"\nmetadata head:\n---\n{metadata.head()}\n---\n")

    # Load all sketches into one object for reference later
    sketches = sourmash_utils.load_sketches(metadata[sig_col], ksize, molecule)
    logger.info(f"\nLoaded {len(sketches)} sourmash signatures/sketches")
    if not sketches:
        # If sketches is empty --> something wrong happened
        sketch_filenames = '\n'.join(metadata[sig_col].head())
        raise ValueError(f"Could not load sourmash signatures/sketches from"
                         f" {metadata_csv}! These are some of the files we couldn't "
                         f"load:\n---\n{sketch_filenames}\n---\nMaybe the molecule or "
                         f"ksize is wrong? Molecule: {molecule} and ksize: {ksize}")
    sketch_series = pd.Series(sketches, index=[x.name() for x in sketches])
    logger.info(f"\nSketch series head: {sketch_series.head()}")

    # If group1 is provided, only do one hash enrichment
    if group1 is not None:
        logger.info(f"\n--- group: {group1} ---")
        coefficients = get_hashes_enriched_in_group(group1, metadata, group_col,
                                                    sketch_series, verbose=verbose, C=C,
                                                    n_jobs=n_jobs, solver=solver,
                                                    penalty=penalty,
                                                    random_state=random_state,
                                                    max_group_size=max_group_size,
                                                    with_abundance=with_abundance)
        write_hash_coefficients(coefficients, group1, threshold)
    else:
        for group1, df in metadata.groupby(group_col):
            logger.info(f"\n--- group: {group1} ---")
            coefficients = get_hashes_enriched_in_group(group1, metadata, group_col,
                                                        sketch_series, verbose=verbose,
                                                        C=C,
                                                        n_jobs=n_jobs, solver=solver,
                                                        penalty=penalty,
                                                        random_state=random_state,
                                                        max_group_size=max_group_size,
                                                        with_abundance=with_abundance)
            write_hash_coefficients(coefficients, group1, threshold)


def write_hash_coefficients(coefficients, group, threshold):
    # No funny characters, and all lowercase, no spaces
    sanitized = sanitize_filename(group).lower().replace(' ', '_')

    # Write hashes with coefficients to file
    csv = f'{sanitized}__hash_coefficients.csv'
    coefficients.to_csv(csv, header=False)

    # Write only hashes above threshold to file
    filtered_coef = coefficients[coefficients > threshold]
    txt = f'{sanitized}__informative_hashes.txt'
    informative_hashes = pd.Series(filtered_coef.index)
    informative_hashes.to_csv(txt, index=False, header=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Perform logistic regression on """)
    parser.add_argument("--metadata-csv", type=str,
                        help="CSV of metadata with columns: sample_id,fasta,sig,group")
    parser.add_argument('-k', '--ksize', type=int, required=True)
    parser.add_argument(
        '--input-is-protein', action='store_true',
        help='Consume protein sequences - no translation needed.'
    )
    parser.add_argument(
        '--with-abundance', action='store_true',
        help='Include hash abundances for differential hash expression'
    )
    parser.add_argument('-g', "--group-col", type=str,
                        default='group',
                        help="Name of column in metadata containing paths to signature "
                             "files ")
    parser.add_argument('-g1', "--group1", type=str,
                        default=None,
                        help="If provided, only do differential hash enrichment"
                             " for this group vs the rest")
    parser.add_argument('-s', "--sig-col", type=str,
                        default='sig',
                        help="Name of column in metadata to group by to find "
                             "differential hash groups")
    parser.add_argument('-t', "--threshold", type=float, default=0,
                        help="Value to use to get high-scoring hashes")
    parser.add_argument("--solver", type=str, default='saga',
                        help="""From scikit-learn Logistic Regression documentation:
Algorithm to use in the optimization problem.
- For small datasets, 'liblinear' is a good choice, whereas 'sag' and 'saga' are faster
  for large ones.
- For multiclass problems, only 'newton-cg', 'sag', 'saga' and 'lbfgs' handle
  multinomial loss; 'liblinear' is limited to one-versus-rest schemes.
- 'newton-cg', 'lbfgs', 'sag' and 'saga' handle L2 or no penalty
- 'liblinear' and 'saga' also handle L1 penalty
- 'saga' also supports 'elasticnet' penalty
- 'liblinear' does not support setting penalty='none'
Note that 'sag' and 'saga' fast convergence is only guaranteed on features with
approximately the same scale. You can preprocess the data with a scaler from
sklearn.preprocessing.""")
    parser.add_argument('-C', "--inverse-regularization-strength", type=float,
                        default=0.1,
                        help="From scikit-learn Logistic Regression documentation: "
                             "Inverse of regularization strength; must be a positive "
                             "float. Like in support vector machines, smaller values "
                             "specify stronger regularization."
                             "\n(aka smaller values --> "
                             "fewer 'informative' features which is easier to follow "
                             "up on)")
    parser.add_argument("--penalty", type=str, default=PENALTY,
                        help="From scikit-learn Logistic Regression documentation: "
                             "Inverse of "
                             "regularization strength; must be a positive float. Like "
                             "in support vector machines, smaller values specify"
                             " stronger regularization. (aka smaller values --> fewer "
                             "'informative' features which is easier to follow up on)")
    parser.add_argument('-p', '--n-jobs', type=int, default=1,
                        help='Number of concurrent processes to use for'
                             ' joblib.Parallel')
    parser.add_argument('-m', '--max-group-size', type=int, default=MAX_GROUP_SIZE,
                        help='If a group is larger than this, subsample random cells '
                             '(using the --random-state) ')
    parser.add_argument('-r', '--random-state', type=int, default=0,
                        help='Set seed of random number generator to ensure '
                             'reproducible results')
    parser.add_argument('-v', "--verbose", action='store_true',
                        help="If true, have lots of output")
    parser.add_argument("--use-sig-basename", action='store_true',
                        help="If true, trim the folder name from the signature path in "
                             "the metadata csv. Useful primarily for Nextflow "
                             "pipelines, as the files needed for each process are soft"
                             " linked into the working folder")

    add_construct_moltype_args(parser)
    args = parser.parse_args()

    # Ensure that protein ksizes are divisible by 3
    if (args.protein or args.dayhoff or args.hp) and not args.input_is_protein:
        if args.ksize % 3 != 0:
            error('protein ksizes must be divisible by 3, sorry!')
            error('bad ksizes: {}', ", ".join(args.ksize))
            sys.exit(-1)

    moltype = calculate_moltype(args)

    main(metadata_csv=args.metadata_csv,
         ksize=args.ksize,
         molecule=moltype,
         group_col=args.group_col,
         group1=args.group1,
         sig_col=args.sig_col,
         threshold=args.threshold,
         verbose=args.verbose,
         C=args.inverse_regularization_strength,
         solver=args.solver,
         penalty=args.penalty,
         n_jobs=args.n_jobs,
         random_state=args.random_state,
         use_sig_basename=args.use_sig_basename,
         max_group_size=args.max_group_size,
         with_abundance=args.with_abundance)
