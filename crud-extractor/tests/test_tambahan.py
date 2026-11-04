"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""
import pytest

from crud.lexer import LexError, TokenType as T, tokenize

def test_dua_kutip_berturut_turut():
    toks = tokenize("SELECT var AS 'O''Brien'")
    assert toks[3].value == "O'Brien"

def test_operator_terpanjang():
    toks = tokenize("<> <= >=")
    assert toks[0].value == "<>" and toks[1].value == "<=" and toks[2].value == ">="