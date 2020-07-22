from pandas_schema import Column, Schema
from pandas_schema.validation import (
    IsDtypeValidation, InListValidation, MatchesPatternValidation)

METADATA_CSV_SCHEMA = Schema([
    Column('sample_id', [MatchesPatternValidation(r'\w')]),
    Column('fasta', [MatchesPatternValidation(r'(.fasta)$')]),
    Column('sig', [MatchesPatternValidation(r'(.sig)$')]),
    Column('group', [MatchesPatternValidation(r'\w')]),
    Column('is_aligned', [InListValidation(['aligned', 'unaligned'])]),
    Column('molecule', [
        InListValidation(['dayhoff', 'hp', 'dna', 'protein'])]),
    Column('ksize', [IsDtypeValidation(int)]),
    Column('scaled', [IsDtypeValidation(int)]),
    Column('num_hashes', [IsDtypeValidation(int)]),
])
