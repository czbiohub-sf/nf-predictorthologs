ifndef CONTAINER
CONTAINER := docker
endif

# Same nextflow run command for everyone
NF_RUN=nextflow run -resume

test: \
	test_bam \
	test_bam_noncoding \
	test_diff_hash \
	test_diff_hash_abundance \
	test_diff_hash_sourmash \
	test_diff_hash_is_aligned \
	test_download_refseq \
	test_existing_database \
	test_fastq \
	test_fastq_paired \
	test_hash2kmer \
	test_input_is_protein \
	test_sambamba \
	test_sencha \
	test_sencha_sambamba \
	test_sourmash_search \
	test_sourmash_makedb



test_bam:
	${NF_RUN} -profile $@,${CONTAINER} .

test_bam_noncoding:
	${NF_RUN} -profile test_bam,${CONTAINER} . --search_noncoding

test_fastq:
	${NF_RUN} -profile $@,${CONTAINER} .

test_fastq_paired:
	${NF_RUN} -profile $@,${CONTAINER} .

test_download_refseq:
	${NF_RUN} -profile $@,${CONTAINER} .

test_diff_hash:
	${NF_RUN} -profile $@,${CONTAINER} .

test_diff_hash_abundance:
	${NF_RUN} -profile $@,${CONTAINER} .

test_existing_database:
	${NF_RUN} -profile $@,${CONTAINER} .

test_hash2kmer:
	${NF_RUN} -profile $@,${CONTAINER} .

test_input_is_protein:
	${NF_RUN} -profile $@,${CONTAINER} .

test_sambamba:
	${NF_RUN} -profile $@,${CONTAINER} .

test_sencha:
	${NF_RUN} -profile $@,${CONTAINER} .

test_sencha_sambamba:
	${NF_RUN} -profile $@,${CONTAINER} .

test_sourmash_search:
	${NF_RUN} -profile $@,${CONTAINER} .

test_sourmash_makedb:
	${NF_RUN} -profile $@,${CONTAINER} .

test_diff_hash_sourmash:
	${NF_RUN} -profile $@,${CONTAINER} .

test_diff_hash_is_aligned:
	${NF_RUN} -profile $@,${CONTAINER} .


# --- Linting --- #

lint: markdownlint yamllint

markdownlint:
	markdownlint . -c .github/markdownlint.yml

yamllint:
	yamllint $(find . -type f -name "*.yml")
	nextflow run -profile $@,${CONTAINER} .
