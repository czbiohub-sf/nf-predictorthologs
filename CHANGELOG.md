# nf-core/predictorthologs: Changelog

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## v1.0dev - [date]

Initial release of nf-core/predictorthologs, created with the [nf-core](http://nf-co.re/) template.

### `Added`

- Updated infrastructure files to nf-core/tools version 1.9

### `Fixed`

### `Dependencies`

- ~Added rsync and unzip tools~ -- Install `rsync` and `unzip` via `apt` because they are incompatible with the taxdmp.zip file from NCBI: ([#4](https://github.com/czbiohub/nf-predictorthologs/issues/14))
  - Actually installed `rsync` via apt in `Dockerfile`, not just `unzip` ([#16](https://github.com/czbiohub/nf-predictorthologs/pull/16))
- Added bedtools=2.29.2 to dependencies
- Added Rust and sourmash ([#24](https://github.com/czbiohub/nf-predictorthologs/pull/24))
- Added pandas=1.0.3, scikit-learn=0.22.1, and sourmash=3.2.2 to dependencies

### `Deprecated`
