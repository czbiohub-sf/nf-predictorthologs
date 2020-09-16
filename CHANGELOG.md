# nf-core/predictorthologs: Changelog

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## v1.0dev - [date]

Initial release of nf-core/predictorthologs, created with the [nf-core](http://nf-co.re/) template.

### `Added`

- Updated infrastructure files to nf-core/tools version 1.9
- Added option for `--input_is_protein`
- Added option for `--differential_hash_expression` performed by scikit-learn's Logistic Regression
- Added option of using sourmash to search instead of DIAMOND. This stays in hash-land by searching hashes (provided by `--hashes` or found by `--differential_hash_expression`) directly into a sourmash sequence bloom tree index database
- Added option for bam deduplication, if you wish to skip deduplication step add the `-skip_remove_duplicates_bam` flag
- Added ability to search DIAMOND for hashes that were unassigned from sourmash ([#79](https://github.com/czbiohub/nf-predictorthologs/pull/79))

### `Fixed`

- Differential hash expression
  - Output differential hash expression hashes and DIAMOND blastp search results into a per-group subfolder
  - Add `--with-abundance` flag to allow for differential expression with tracked abundances
- `hash2kmer.py` ignores empty lines
- Fixed polyX trimming for paired-end fastqs ([#66](https://github.com/czbiohub/nf-predictorthologs/pull/66))
- Fixed paired-end reads getting removed after trimming ([#75](https://github.com/czbiohub/nf-predictorthologs/pull/75))
- Fixed number of cpus, memory, time requirements for sambamba processes ([#76](https://github.com/czbiohub/nf-predictorthologs/pull/76))
- Fixed noncoding search to use `cmscan` instead of `cmsearch` from INFERNAL ([#74](https://github.com/czbiohub/nf-predictorthologs/pull/74))
- Propagate molecule and k-mer size to sample id after translate

### `Dependencies`

- Added 7z (`bioconda==p7zip=15.09`) to deal with compatibilities of bioconda's `unzip` the taxdmp.zip file from NCBI: ([#14](https://github.com/czbiohub/nf-predictorthologs/issues/14))
- Added rsync to download NCBI RefSeq releases
- Actually installed `rsync` via apt in `Dockerfile`, not just `unzip` ([#16](https://github.com/czbiohub/nf-predictorthologs/pull/16))
- Added bedtools=2.29.2 to dependencies
- Added Rust (required for compiling sourmash from GitHub) ([#24](https://github.com/czbiohub/nf-predictorthologs/pull/24))
- Added pandas=1.0.3, scikit-learn=0.22.1, and sourmash=3.2.2 to dependencies
- Added subread=1.6.4 (featurecounts) and bioawk=1.0
- Updated MultiQC to version 1.8 to avoid annoying YAML errors
- Add ripgrep=12.0.1 ([faster than all other `grep`s](https://blog.burntsushi.net/ripgrep/)) to dependencies
- Updated sourmash=3.3.0 ([#46](https://github.com/czbiohub/nf-predictorthologs/pull/46)) to support zip files as indices
- Added csvtk=0.20.0 to dependencies
- Addeed infernal=1.1.2 to dependencies
- Update DIAMOND to version 0.9.35 to deal with new NCBI taxonomy formats
- Added sambamba=0.7.1 using bioconda channel

### `Deprecated`
