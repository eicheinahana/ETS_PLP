"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""
import pytest

# LEXER
from crud.lexer import LexError, TokenType as T, tokenize

def test_dua_kutip_berturut_turut():
    toks = tokenize("SELECT var AS 'O''Brien'")
    assert toks[3].value == "O'Brien"

def test_operator_terpanjang():
    toks = tokenize("<> <= >=")
    assert toks[0].value == "<>" and toks[1].value == "<=" and toks[2].value == ">="


# PARSER
from crud import ast_nodes as ast
from crud.parser import parse_sql
from test_parser import one

def test_hanya_statement_gagal_yang_dibuang():
    s = parse_sql("SELECT id FROM ; \n SELECT nama FROM pelanggan;")
    assert len(s.errors) == 1
    assert len(s.statements) == 1
    assert s.statements[0].line == 2
    assert s.statements[0].sources[0].name == "pelanggan"

def test_left_outer_join():
    s = one("SELECT a.id FROM a LEFT OUTER JOIN b ON b.a_id = a.id")
    assert s.joins[0].kind == "LEFT"
    assert s.joins[0].source.name == "b"