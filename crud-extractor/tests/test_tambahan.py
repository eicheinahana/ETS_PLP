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

def test_and_didahulukan_dari_or():
    s = one("SELECT a FROM t WHERE x = 1 OR y = 2 AND z = 3")
    assert isinstance(s.where, ast.BinaryOp) and s.where.op == "OR"
    assert isinstance(s.where.right, ast.BinaryOp) and s.where.right.op == "AND"


# ====================================================================
# TAMBAHAN BARU: regresi bug 1, 7, 8, 9 + test untuk T1, T2, T3 + 5 kasus tepi
# ====================================================================
from crud.analyzer import analyze_statement
from crud.pipeline import analyze_source
from crud.resolver import Resolver


def _resolve(sql):
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    return script, Resolver().resolve_script(script)


def _kolom(script):
    return [n for n in ast.iter_nodes(script) if isinstance(n, ast.ColumnRef)]


# ---- regresi bug ---------------------------------------------------
def test_keyword_huruf_kecil_jadi_besar():
    # bug 1: keyword tidak peka huruf besar/kecil (spesifikasi 2.2)
    for sumber in ("select id from t", "Select id From t"):
        toks = tokenize(sumber)
        assert toks[0].type == T.KEYWORD and toks[0].value == "SELECT"
        assert toks[2].type == T.KEYWORD and toks[2].value == "FROM"
        assert toks[1].type == T.IDENT


def test_alias_subquery_menutupi_alias_luar():
    # bug 7: pencarian alias harus dari scope terdalam ke luar (spesifikasi 4.3)
    script, diags = _resolve(
        "SELECT 1 FROM a x WHERE EXISTS (SELECT 1 FROM b x WHERE x.id = 1)")
    assert [c.resolved for c in _kolom(script)] == ["b"]
    assert diags == []


def test_scope_tidak_bocor_antar_statement():
    # bug 8: DELETE harus menutup scope-nya (spesifikasi 4.5)
    script, diags = _resolve("DELETE FROM a z; SELECT z.id FROM b;")
    assert _kolom(script)[0].resolved is None
    assert any(d.level == "error" and "'z'" in d.message for d in diags)


def test_subquery_di_update_dibaca_R():
    # bug 9: membaca tabel lewat subquery selalu R (spesifikasi 5)
    script = parse_sql("UPDATE a SET x = 1 WHERE id IN (SELECT id FROM b)")
    assert analyze_statement(script.statements[0]) == {"a": {"U"}, "b": {"R"}}


# ---- test untuk bagian TODO ------------------------------------------
def test_komentar_blok_tidak_ditutup_adalah_lexerror():
    # T3, spesifikasi 2.3
    with pytest.raises(LexError):
        tokenize("SELECT /* tidak ditutup")


def test_insert_select_matrix():
    # T1, spesifikasi 5: target C, sumber R
    hasil = analyze_source("INSERT INTO arsip (id) SELECT id FROM pesanan")
    assert hasil.matrix() == {"arsip": "C", "pesanan": "R"}


def test_kolom_tanpa_qualifier_satu_tabel_dan_ambigu():
    # T2, spesifikasi 4.3: satu tabel -> di-resolve; dua tabel -> warning dan None
    script, diags = _resolve("SELECT nama FROM pelanggan")
    assert [c.resolved for c in _kolom(script)] == ["pelanggan"]
    script, diags = _resolve("SELECT nama FROM pelanggan p JOIN pesanan o ON p.id = o.pid")
    nama = [c for c in _kolom(script) if c.name == "nama"][0]
    assert nama.resolved is None
    assert any(d.level == "warning" and "ambigu" in d.message for d in diags)


# ---- 5 test kasus tepi -----------------------------------------------
def test_tepi_titik_koma_kosong():
    # ';;;' sah menurut grammar (script = { ";" | ... }); kode bisa salah mengira
    # setiap ';' pasti didahului statement.
    s = parse_sql(";;;")
    assert s.errors == [] and s.statements == []


def test_tepi_komentar_blok_kosong():
    # '/**/': penutup muncul tepat setelah pembuka; pemindai bisa salah menunggu isi dulu.
    toks = tokenize("/**/ SELECT")
    assert [t.type for t in toks[:-1]] == [T.KEYWORD]


def test_tepi_string_kosong_dan_satu_kutip():
    # dua kutip = string kosong, empat kutip = satu karakter kutip; aturan dua kutip
    # berturut-turut di dalam string bisa salah mengenali string kosong.
    assert tokenize("''")[0].value == ""
    assert tokenize("''''")[0].value == "'"


def test_tepi_subquery_from_tanpa_alias_hanya_warning():
    # spesifikasi 4.2: tanpa alias hanya warning; kode bisa menganggapnya error.
    _, diags = _resolve("SELECT 1 FROM (SELECT a FROM t)")
    assert [d.level for d in diags] == ["warning"]


def test_tepi_insert_select_dari_tabel_sama():
    # satu tabel harus mendapat C dan R sekaligus, ditulis berurutan 'CR'.
    hasil = analyze_source("INSERT INTO t SELECT a FROM t")
    assert hasil.matrix() == {"t": "CR"}