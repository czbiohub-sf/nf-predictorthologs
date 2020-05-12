# nf-core/predictorthologs: Changelog

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## v1.0dev - [date]

Initial release of nf-core/predictorthologs, created with the [nf-core](http://nf-co.re/) template.

### `Added`

- Updated infrastructure files to nf-core/tools version 1.9
- Added option for `--input_is_protein`
- Added option for `--diff_hash_expression` performed by scikit-learn's Logistic Regression, if `--csv` is provided with at least columns `sample_id`, `sig` and `group`
- Added option of using sourmash to search instead of DIAMOND. This stays in hash-land by searching hashes (provided by `--hashes` or found by `--diff_hash_expression`) directly into a sourmash sequence bloom tree index database
- Added ability to filter `bam` file for reads containing hashes, if the `--csv` contains a column named `bam` and the option `--filter-bam-hashes` is provided

### `Fixed`

- Differential hash expression
  - Output differential hash expression hashes and DIAMOND blastp search results into a per-group subfolder
  - Add `--with-abundance` flag to allow for differential expression with tracked abundances
- `hash2kmer.py` ignores empty lines

### `Dependencies`

- Added 7z (`bioconda==p7zip=15.09`) to deal with compatibilities of bioconda's `unzip` the taxdmp.zip file from NCBI: ([#14](https://github.com/czbiohub/nf-predictorthologs/issues/14))
- Added rsync to download NCBI RefSeq releases
- Actually installed `rsync` via apt in `Dockerfile`, not just `unzip` ([#16](https://github.com/czbiohub/nf-predictorthologs/pull/16))
- Added bedtools=2.29.2 to dependencies
- Added sourmash Rust (required for compiling sourmash from GitHub) ([#24](https://github.com/czbiohub/nf-predictorthologs/pull/24))
- Added pandas=1.0.3, scikit-learn=0.22.1, and sourmash=3.2.2 to dependencies
- Added subread=1.6.4 (featurecounts) and bioawk=1.0
- Updated MultiQC to version 1.8 to avoid annoying YAML errors
- Add ripgrep=12.0.1 ([faster than all other `grep`s](https://blog.burntsushi.net/ripgrep/)) to dependencies

### `Deprecated`
