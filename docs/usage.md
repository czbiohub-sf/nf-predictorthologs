# nf-core/predictorthologs: Usage

## Table of contents

<!-- TOC depthFrom:1 depthTo:6 withLinks:1 updateOnSave:0 orderedList:0 -->

- [nf-core/predictorthologs: Usage](#nf-corepredictorthologs-usage)
  - [Table of contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Running the pipeline](#running-the-pipeline)
    - [Updating the pipeline](#updating-the-pipeline)
    - [Reproducibility](#reproducibility)
  - [Main arguments](#main-arguments)
    - [`-profile`](#-profile)
    - [`--reads`](#-reads)
    - [`--single_end`](#-singleend)
    - [`--csv`](#-csv)
      - [Simple fasta input](#simple-fasta-input)
    - [Differential hash expression](#differential-hash-expression)
  - [Reference proteomes](#reference-proteomes)
    - [Proteomes for translating](#proteomes-for-translating)
      - [`--proteome_translate_fasta`](#-proteometranslatefasta)
      - [`--translate_peptide_ksize` & `--translate_peptide_molecule`](#-translatepeptideksize-translatepeptidemolecule)
    - [Proteomes for searching](#proteomes-for-searching)
      - [`--refseq_release` (using NCBI RefSeq)](#-refseqrelease-using-ncbi-refseq)
      - [`--proteome_search_fasta`](#-proteomesearchfasta)
  - [Job resources](#job-resources)
    - [Automatic resubmission](#automatic-resubmission)
    - [Custom resource requests](#custom-resource-requests)
  - [AWS Batch specific parameters](#aws-batch-specific-parameters)
    - [`--awsqueue`](#-awsqueue)
    - [`--awsregion`](#-awsregion)
    - [`--awscli`](#-awscli)
  - [Other command line parameters](#other-command-line-parameters)
    - [`--outdir`](#-outdir)
    - [`--email`](#-email)
    - [`--email_on_fail`](#-emailonfail)
    - [`--max_multiqc_email_size`](#-maxmultiqcemailsize)
    - [`-name`](#-name)
    - [`-resume`](#-resume)
    - [`-c`](#-c)
    - [`--custom_config_version`](#-customconfigversion)
    - [`--custom_config_base`](#-customconfigbase)
  - [Download and unzip the config files](#download-and-unzip-the-config-files)
  - [Run the pipeline](#run-the-pipeline)
    - [`--max_memory`](#-maxmemory)
    - [`--max_time`](#-maxtime)
    - [`--max_cpus`](#-maxcpus)
    - [`--plaintext_email`](#-plaintextemail)
    - [`--monochrome_logs`](#-monochromelogs)
    - [`--multiqc_config`](#-multiqcconfig)

<!-- /TOC -->

## Introduction

Nextflow handles job submissions on SLURM or other environments, and supervises running the jobs. Thus the Nextflow process must run until the pipeline is finished. We recommend that you put the process running in the background through `screen` / `tmux` or similar tool. Alternatively you can run nextflow within a cluster job submitted your job scheduler.

It is recommended to limit the Nextflow Java virtual machines memory. We recommend adding the following line to your environment (typically in `~/.bashrc` or `~./bash_profile`):

```bash
NXF_OPTS='-Xms1g -Xmx4g'
```

<!-- TODO nf-core: Document required command line parameters to run the pipeline-->

## Running the pipeline

The typical command for running the pipeline is as follows:

```bash
nextflow run nf-core/predictorthologs --reads '*_R{1,2}.fastq.gz' -profile docker
```

This will launch the pipeline with the `docker` configuration profile. See below for more information about profiles.

Note that the pipeline will create the following files in your working directory:

```bash
work            # Directory containing the nextflow working files
results         # Finished results (configurable, see below)
.nextflow_log   # Log file from Nextflow
# Other nextflow hidden files, eg. history of pipeline runs and old logs.
```

### Updating the pipeline

When you run the above command, Nextflow automatically pulls the pipeline code from GitHub and stores it as a cached version. When running the pipeline after this, it will always use the cached version if available - even if the pipeline has been updated since. To make sure that you're running the latest version of the pipeline, make sure that you regularly update the cached version of the pipeline:

```bash
nextflow pull nf-core/predictorthologs
```

### Reproducibility

It's a good idea to specify a pipeline version when running the pipeline on your data. This ensures that a specific version of the pipeline code and software are used when you run your pipeline. If you keep using the same tag, you'll be running the same version of the pipeline, even if there have been changes to the code since.

First, go to the [nf-core/predictorthologs releases page](https://github.com/nf-core/predictorthologs/releases) and find the latest version number - numeric only (eg. `1.3.1`). Then specify this when running the pipeline with `-r` (one hyphen) - eg. `-r 1.3.1`.

This version number will be logged in reports when you run the pipeline, so that you'll know what you used when you look back in the future.

## Main arguments

### `-profile`

Use this parameter to choose a configuration profile. Profiles can give configuration presets for different compute environments.

Several generic profiles are bundled with the pipeline which instruct the pipeline to use software packaged using different methods (Docker, Singularity, Conda) - see below.

> We highly recommend the use of Docker or Singularity containers for full pipeline reproducibility, however when this is not possible, Conda is also supported.

The pipeline also dynamically loads configurations from [https://github.com/nf-core/configs](https://github.com/nf-core/configs) when it runs, making multiple config profiles for various institutional clusters available at run time. For more information and to see if your system is available in these configs please see the [nf-core/configs documentation](https://github.com/nf-core/configs#documentation).

Note that multiple profiles can be loaded, for example: `-profile test,docker` - the order of arguments is important!
They are loaded in sequence, so later profiles can overwrite earlier profiles.

If `-profile` is not specified, the pipeline will run locally and expect all software to be installed and available on the `PATH`. This is _not_ recommended.

- `docker`
  - A generic configuration profile to be used with [Docker](http://docker.com/)
  - Pulls software from dockerhub: [`nfcore/predictorthologs`](http://hub.docker.com/r/nfcore/predictorthologs/)
- `singularity`
  - A generic configuration profile to be used with [Singularity](http://singularity.lbl.gov/)
  - Pulls software from DockerHub: [`nfcore/predictorthologs`](http://hub.docker.com/r/nfcore/predictorthologs/)
- `conda`
  - Please only use Conda as a last resort i.e. when it's not possible to run the pipeline with Docker or Singularity.
  - A generic configuration profile to be used with [Conda](https://conda.io/docs/)
  - Pulls most software from [Bioconda](https://bioconda.github.io/)
- `test`
  - A profile with a complete configuration for automated testing
  - Includes links to test data so needs no other parameters

<!-- TODO nf-core: Document required command line parameters -->

### `--reads`

Use this to specify the location of your input FastQ files. For example:

```bash
--reads 'path/to/data/sample_*_{1,2}.fastq'
```

Please note the following requirements:

1. The path must be enclosed in quotes
2. The path must have at least one `*` wildcard character
3. When using the pipeline with paired end data, the path must use `{1,2}` notation to specify read pairs.

If left unspecified, a default pattern is used: `data/*{1,2}.fastq.gz`

### `--single_end`

By default, the pipeline expects paired-end data. If you have single-end data, you need to specify `--single_end` on the command line when you launch the pipeline. A normal glob pattern, enclosed in quotation marks, can then be used for `--reads`. For example:

```bash
--single_end --reads '*.fastq'
```

It is not possible to run a mixture of single-end and paired-end files in one run.

### `--csv`

Input a csv of sample ids and fasta filenames

#### Simple fasta input

The simplest input of fastas is a csv that looks like:

```bash
sample_id,fasta
sample1,sample1.fasta
sample2,sample2.fasta
```

### Differential hash expression

To do differential hash expression and then search for the enriched hashes in a database, the csv needs to contain the following columns:

- `sample_id`: a uniquely identifying name
- `fasta`: path to (translated protein) fasta file for the sample
- `sig`: path to a sourmash signature file for the sample
- `group`: a filepath-friendly name (no weird characters like `/` or `|`) of the group, to subset the data on

Additionally, the parameters `--sourmash_ksize` and `--sourmash_molecule` must be provided.

Here is an example signature:

```bash
sample_id,fasta,group,sig
sample1,sample1__coding_reads_peptides.fasta,Mostly marrow unaligned,sample1_molecule-dayhoff_ksize-45_log2sketchsize-14_trackabundance-true.sig
sample2,sample2__coding_reads_peptides.fasta,Mostly marrow unaligned,sample2_molecule-dayhoff_ksize-45_log2sketchsize-14_trackabundance-true.sig
sample3,sample3__coding_reads_peptides.fasta,Mostly marrow unaligned,sample3_molecule-dayhoff_ksize-45_log2sketchsize-14_trackabundance-true.sig
sample4,sample4__coding_reads_peptides.fasta,Mostly marrow unaligned,sample4_molecule-dayhoff_ksize-45_log2sketchsize-14_trackabundance-true.sig
sample5,sample5__coding_reads_peptides.fasta,Mostly marrow unaligned,sample5_molecule-dayhoff_ksize-45_log2sketchsize-14_trackabundance-true.sig
sample6,sample6__coding_reads_peptides.fasta,Liver unaligned,sample6_molecule-dayhoff_ksize-45_log2sketchsize-14_trackabundance-true.sig
sample7,sample7__coding_reads_peptides.fasta,Liver unaligned,sample7_molecule-dayhoff_ksize-45_log2sketchsize-14_trackabundance-true.sig
sample8,sample8__coding_reads_peptides.fasta,Liver unaligned,sample8_molecule-dayhoff_ksize-45_log2sketchsize-14_trackabundance-true.sig
sample9,sample9__coding_reads_peptides.fasta,Liver unaligned,sample9_molecule-dayhoff_ksize-45_log2sketchsize-14_trackabundance-true.sig
sample10,sample10__coding_reads_peptides.fasta,Liver unaligned,sample10_molecule-dayhoff_ksize-45_log2sketchsize-14_trackabundance-true.sig
```

## Reference proteomes

There are two different kinds of reference proteomes used in this pipeline:

- **Reference proteome for translation**, `--proteome_translate_fasta`
  - In general, it is desirable for this first proteome used for translation is a very conservative set of highly curated protein sequences, such as manually curated from UniProt/SwissProt.
  - The reason for this is that it is not desirable to have false positives when translating the sequences, and to only have highly trustworthy translated sequences for downstream processing
- **Reference proteome for searching translated proteins**, `--proteome_search_fasta`
  - This proteome for searching can be more permissive (a superset of above) as this is used for searching, and we're interested in casting the widest net for finding potential matches, thus we recommend RefSeq over UniProt as their submission guidelines are more permissive.
  - A caveat is that in RefSeq, there are also many dubious sequences, and fortunately these are easy to find with the identifier. Sequence IDs that start with `NP_` are the most trustworthy as they have an associated `NM_` (protein-coding RNA transcirpt) or `NC_` (complete genomic molecule) accessions. Read more about the wild, wild world of NCBI accession ids [here](https://www.ncbi.nlm.nih.gov/books/NBK21091/table/ch18.T.refseq_accession_numbers_and_mole/?report=objectonly)

### Proteomes for translating

#### `--proteome_translate_fasta`

We recommend using manually curated sequences from UniProt/SwissProt. By default, we use the Human reference proteome `ftp://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/reference_proteomes/Eukaryota/UP000005640_9606.fasta.gz`. If your organism of interest is closely related to any of the organisms in the [Reference Proteomes](https://www.ebi.ac.uk/reference_proteomes/) dataset, we recommend using that.

If you are using a broad dataset of many species, we recommend combining their manually curated proteomes into one, or using UniProt's website to download all the manually curated sequences for that clade.

#### `--translate_peptide_ksize` & `--translate_peptide_molecule`

These parameters influence how the translated sequences are pulled out.

Here are our recommendations for a variety of divergence times:

- Closely related (<100 million years diverged), e.g. human and mouse:
  - `--translate_peptide_molecule protein`
  - `--translate_peptide_ksize 9`
- Medium-diverged (100 million years ago < x < 500 million years ago), e.g. human and zebrafish:
  - `--translate_peptide_molecule dayhoff`
  - `--translate_peptide_ksize 15`
- Largely-diverged (500 million years ago < x < 1000 million years ago), e.g. Bilateria:
  - `--translate_peptide_molecule hp`
  - `--translate_peptide_ksize 45`

### Proteomes for searching

#### `--refseq_release` (using NCBI RefSeq)

There are 31 different species supported in the iGenomes references. To run the pipeline, you must specify which to use with the `--genome` flag.

Common proteomes that are supported are valid terms from [NCBI RefSeq Releases](ftp://ftp.ncbi.nlm.nih.gov/refseq/release/). We recommend using the narrowest group for your particular search of interest. E.g. if you are searching within mammals, use the "vertebrate_mammalian" group

- RefSeq Complete
  - `--refseq_release complete`
- Archea
  - `--refseq_release archea`
- Bacteria
  - `--refseq_release bacteria`
- Fungi
  - `--refseq_release fungi`
- Invertebrate
  - `--refseq_release invertebrate`
- Mitochondria
  - `--refseq_release mitochondrion`
- Other
  - `--refseq_release other`
- Plant
  - `--refseq_release plant`
- Plasmid
  - `--refseq_release plasmid`
- Plastid
  - `--refseq_release plastid`
- Vertebrate (Mammals)
  - `--refseq_release vertebrate_mammalian`
- Vertebrate (Other)
  - `--refseq_release vertebrate_other`
- Viral
  - `--refseq_release viral`

<!-- TODO nf-core: Describe reference path flags -->

#### `--proteome_search_fasta`

If you prefer, you can specify the full path to your reference genome when you run the pipeline:

```bash
--proteome_search_fasta '[path to Proteome Fasta reference]'
```

## Job resources

### Automatic resubmission

Each step in the pipeline has a default set of requirements for number of CPUs, memory and time. For most of the steps in the pipeline, if the job exits with an error code of `143` (exceeded requested resources) it will automatically resubmit with higher requests (2 x original, then 3 x original). If it still fails after three times then the pipeline is stopped.

### Custom resource requests

Wherever process-specific requirements are set in the pipeline, the default value can be changed by creating a custom config file. See the files hosted at [`nf-core/configs`](https://github.com/nf-core/configs/tree/master/conf) for examples.

If you are likely to be running `nf-core` pipelines regularly it may be a good idea to request that your custom config file is uploaded to the `nf-core/configs` git repository. Before you do this please can you test that the config file works with your pipeline of choice using the `-c` parameter (see definition below). You can then create a pull request to the `nf-core/configs` repository with the addition of your config file, associated documentation file (see examples in [`nf-core/configs/docs`](https://github.com/nf-core/configs/tree/master/docs)), and amending [`nfcore_custom.config`](https://github.com/nf-core/configs/blob/master/nfcore_custom.config) to include your custom profile.

If you have any questions or issues please send us a message on [Slack](https://nf-co.re/join/slack).

## AWS Batch specific parameters

Running the pipeline on AWS Batch requires a couple of specific parameters to be set according to your AWS Batch configuration. Please use [`-profile awsbatch`](https://github.com/nf-core/configs/blob/master/conf/awsbatch.config) and then specify all of the following parameters.

### `--awsqueue`

The JobQueue that you intend to use on AWS Batch.

### `--awsregion`

The AWS region in which to run your job. Default is set to `eu-west-1` but can be adjusted to your needs.

### `--awscli`

The [AWS CLI](https://www.nextflow.io/docs/latest/awscloud.html#aws-cli-installation) path in your custom AMI. Default: `/home/ec2-user/miniconda/bin/aws`.

Please make sure to also set the `-w/--work-dir` and `--outdir` parameters to a S3 storage bucket of your choice - you'll get an error message notifying you if you didn't.

## Other command line parameters

<!-- TODO nf-core: Describe any other command line flags here -->

### `--outdir`

The output directory where the results will be saved.

### `--email`

Set this parameter to your e-mail address to get a summary e-mail with details of the run sent to you when the workflow exits. If set in your user config file (`~/.nextflow/config`) then you don't need to specify this on the command line for every run.

### `--email_on_fail`

This works exactly as with `--email`, except emails are only sent if the workflow is not successful.

### `--max_multiqc_email_size`

Threshold size for MultiQC report to be attached in notification email. If file generated by pipeline exceeds the threshold, it will not be attached (Default: 25MB).

### `-name`

Name for the pipeline run. If not specified, Nextflow will automatically generate a random mnemonic.

This is used in the MultiQC report (if not default) and in the summary HTML / e-mail (always).

**NB:*- Single hyphen (core Nextflow option)

### `-resume`

Specify this when restarting a pipeline. Nextflow will used cached results from any pipeline steps where the inputs are the same, continuing from where it got to previously.

You can also supply a run name to resume a specific run: `-resume [run-name]`. Use the `nextflow log` command to show previous run names.

**NB:*- Single hyphen (core Nextflow option)

### `-c`

Specify the path to a specific config file (this is a core NextFlow command).

**NB:*- Single hyphen (core Nextflow option)

Note - you can use this to override pipeline defaults.

### `--custom_config_version`

Provide git commit id for custom Institutional configs hosted at `nf-core/configs`. This was implemented for reproducibility purposes. Default: `master`.

```bash
## Download and use config file with following git commid id
--custom_config_version d52db660777c4bf36546ddb188ec530c3ada1b96
```

### `--custom_config_base`

If you're running offline, nextflow will not be able to fetch the institutional config files
from the internet. If you don't need them, then this is not a problem. If you do need them,
you should download the files from the repo and tell nextflow where to find them with the
`custom_config_base` option. For example:

```bash
## Download and unzip the config files
cd /path/to/my/configs
wget https://github.com/nf-core/configs/archive/master.zip
unzip master.zip

## Run the pipeline
cd /path/to/my/data
nextflow run /path/to/pipeline/ --custom_config_base /path/to/my/configs/configs-master/
```

> Note that the nf-core/tools helper package has a `download` command to download all required pipeline
> files + singularity containers + institutional configs in one go for you, to make this process easier.

### `--max_memory`

Use to set a top-limit for the default memory requirement for each process.
Should be a string in the format integer-unit. eg. `--max_memory '8.GB'`

### `--max_time`

Use to set a top-limit for the default time requirement for each process.
Should be a string in the format integer-unit. eg. `--max_time '2.h'`

### `--max_cpus`

Use to set a top-limit for the default CPU requirement for each process.
Should be a string in the format integer-unit. eg. `--max_cpus 1`

### `--plaintext_email`

Set to receive plain-text e-mails instead of HTML formatted.

### `--monochrome_logs`

Set to disable colourful command line output and live life in monochrome.

### `--multiqc_config`

Specify a path to a custom MultiQC configuration file.
