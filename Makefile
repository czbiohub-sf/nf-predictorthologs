ifndef CONTAINER
CONTAINER := docker
endif

# Same nextflow run command for everyone
NF_RUN=nextflow run -resume

test: test_fastq test_bam test_download_refseq test_existing_database test_hash2kmer test_input_is_protein test_diff_hash test_diff_hash_abundance test_sourmash_search test_diff_hash_sourmash test_diff_hash_is_aligned

test_fastq:
	${NF_RUN} -profile $@,${CONTAINER} .

test_download_refseq:
	${NF_RUN} -profile $@,${CONTAINER} .

test_existing_database:
	${NF_RUN} -profile $@,${CONTAINER} .

test_bam:
	${NF_RUN} -profile $@,${CONTAINER} .

test_input_is_protein:
	${NF_RUN} -profile $@,${CONTAINER} .

test_hash2kmer:
	${NF_RUN} -profile $@,${CONTAINER} .

test_diff_hash:
	${NF_RUN} -profile $@,${CONTAINER} .

test_diff_hash_abundance:
	${NF_RUN} -profile $@,${CONTAINER} . --with_abundance

test_sourmash_search:
	${NF_RUN} -profile $@,${CONTAINER} .

test_diff_hash_sourmash:
	${NF_RUN} -profile $@,${CONTAINER} .

test_diff_hash_is_aligned:
	${NF_RUN} -profile $@,${CONTAINER} .


test_diff_hash_filter_bam_hashes:
	${NF_RUN} -profile $@,${CONTAINER} .


# --- Linting --- #

lint: markdownlint yamllint

markdownlint:
	markdownlint . -c .github/markdownlint.yml

yamllint:
	yamllint $(find . -type f -name "*.yml")
	nextflow run -profile $@,${CONTAINER} .
