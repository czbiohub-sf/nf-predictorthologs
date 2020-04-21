ifndef CONTAINER
CONTAINER := docker
endif

test: test_fastq test_bam test_download_refseq test_existing_database test_hash2kmer test_input_is_protein test_diff_hash test_diff_hash_abundance test_sourmash_search test_diff_hash_sourmash

test_fastq:
	nextflow run -profile $@,${CONTAINER} .

test_download_refseq:
	nextflow run -profile $@,${CONTAINER} .

test_existing_database:
	nextflow run -profile $@,${CONTAINER} .

test_bam:
	nextflow run -profile $@,${CONTAINER} .

test_input_is_protein:
	nextflow run -profile $@,${CONTAINER} .

test_hash2kmer:
	nextflow run -profile $@,${CONTAINER} .

test_diff_hash:
	nextflow run -profile $@,${CONTAINER} .

test_diff_hash_abundance:
	nextflow run -profile $@,${CONTAINER} . --with_abundance
test_sourmash_search:
	nextflow run -profile $@,${CONTAINER} .

test_diff_hash_sourmash:
	nextflow run -profile $@,${CONTAINER} .

# --- Linting --- #

lint: markdownlint yamllint

markdownlint:
	markdownlint . -c .github/markdownlint.yml

yamllint:
	yamllint $(find . -type f -name "*.yml")
