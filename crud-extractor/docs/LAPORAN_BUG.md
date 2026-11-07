# Laporan Bug

Ringkasan: 9 bug ditemukan dan diperbaiki, ditambah 3 bagian TODO (T1, T2, T3) yang dilengkapi.
Urutan bug mengikuti alur pipeline: lexer (1-3), parser (4-6), resolver (7-8), analyzer (9).
Setiap bug punya test regresi di `tests/test_tambahan.py` yang gagal pada kode lama dan lulus
pada kode baru.

| No | Bug | Pos | Bagian spesifikasi |
| --- | --- | --- | --- |
| 1 | Keyword huruf kecil dibaca sebagai nama biasa | lexer | 2.2 |
| 2 | Dua kutip berturut-turut di dalam string memotong string | lexer | 2.4 |
| 3 | Operator `<>` terpotong menjadi dua token | lexer | 2.5 |
| 4 | Pemulihan error membuang semua statement sesudahnya | parser | 5, 6 |
| 5 | `LEFT OUTER JOIN` ditolak | parser | 3 |
| 6 | `AND` dan `OR` diperlakukan setingkat | parser | 3.1 |
| 7 | Urutan pencarian alias scope terbalik | resolver | 4.3 |
| 8 | Scope `DELETE` tidak ditutup, alias bocor | resolver | 4.5 |
| 9 | Tabel di subquery `UPDATE` dihitung U, seharusnya R | analyzer | 5 |

---

## Bug 1: Keyword huruf kecil dibaca sebagai nama biasa

**Ditemukan oleh:** Upi dan Hana Mardhiyyah (test terlihat `test_keyword_huruf_kecil` gagal) · **Diperbaiki oleh:** Hana Mardhiyyah (commit `afe9534`)

**Gejala.** Input `select id from t`. Output yang didapat: token pertama bertipe `IDENT` bernilai
`select`. Output yang diharapkan: `KEYWORD` bernilai `SELECT`, karena keyword tidak peka huruf
besar/kecil dan nilainya dinormalisasi ke huruf besar (SPESIFIKASI.md bagian 2.2).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
select id from t
```

**Akar masalah.** Lexer mencocokkan teks kata apa adanya dengan daftar `KEYWORDS` yang seluruhnya
huruf besar, sehingga `select` huruf kecil tidak cocok dan jatuh menjadi nama biasa (`IDENT`).
Spesifikasi menuntut keyword tidak peka huruf besar/kecil, jadi lexer harus menormalisasi kata
dulu sebelum membandingkannya. Dalam istilah buku, tahap pembacaan kata memutuskan apakah suatu
kata adalah *reserved word* atau *identifier*, dan keputusan itu salah karena perbandingannya
peka huruf. Rujukan: Bab 4, *Reserved Words and Identifiers*.

**Perbaikan.** `crud/lexer.py`, fungsi `_word`: kata diubah ke huruf besar untuk dicek ke
`KEYWORDS`; bila cocok, token bertipe `KEYWORD` bernilai huruf besar; bila tidak, token `IDENT`
tetap memakai huruf aslinya (parser yang kemudian menurunkannya ke huruf kecil). Alternatif yang
dipertimbangkan: menormalisasi di parser. Tidak dipilih karena spesifikasi 2.2 menetapkan nilai
token keyword sudah huruf besar sejak dari lexer, dan parser tidak perlu tahu huruf aslinya.

**Test regresi.** `test_keyword_huruf_kecil_jadi_besar` di `tests/test_tambahan.py`.

**Peran AI.** AI (Claude) membantu Upi memahami dan mereviu perbaikan ini setelah dikerjakan Hana.
Diverifikasi dengan menjalankan `pytest` dan membaca perubahan kode di GitHub.
Penggunaan AI oleh Hana untuk bug ini: [Hana isi, atau hapus kalimat ini].

---

## Bug 2: Satu karakter kutip tidak terbaca (dua kutip berturut-turut di dalam string)

**Ditemukan oleh:** Hana Mardhiyyah · **Diperbaiki oleh:** Hana Mardhiyyah (commit `4854bdb`)

**Gejala.** Input: `SELECT var AS 'O''Brien'`.
Output yang didapat: `[Token(KEYWORD, 'SELECT', 1:1), Token(IDENT, 'var', 1:8), Token(KEYWORD, 'AS', 1:12), Token(STRING, 'O', 1:15), Token(STRING, 'Brien', 1:18), Token(EOF, '', 1:25)]`.
Output yang diharapkan: `[Token(KEYWORD, 'SELECT', 1:1), Token(IDENT, 'var', 1:8), Token(KEYWORD, 'AS', 1:12), Token(STRING, "O'Brien", 1:15), Token(EOF, '', 1:25)]`
(SPESIFIKASI.md bagian 2.4).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT 'O''Brien'
```

**Akar masalah.** Kode lama salah karena tidak melihat terlebih dahulu karakter selanjutnya apakah
tanda kutip (') atau bukan. Sehingga, langsung mengakhiri input karakter ketika karakternya adalah
tanda kutip ('). Kode tidak menerapkan lookahead pada Bab 4: Scanning. Lookahead adalah proses
mengintip karakter selanjutnya untuk dicocokkan. Lookahead akan mengintip karakter selanjutnya
untuk memutuskan apakah tanda kutip (') tersebut menandakan karakter tanda kutip atau akhir dari
sebuah string.

**Perbaikan.** File yang diubah: `lexer.py`. Fungsi yang diubah: `_string()`.
Alasan: karena `'O''Brien'` menjadi `O'Brien` merupakan bagian dari scanning. Scanning mengubah
data mentah menjadi nilai yang akan diproses. Sehingga, file yang diubah adalah `lexer.py`. Fungsi
`_string()` diubah karena fungsi tersebut memproses string yang diawali dengan tanda kutip (')
dari `_scan_token()` yang kemudian dilanjutkan ke fungsi `_string()` untuk diproses.

Perbaikan alternatif:

```python
if ch == "'" and not self._match("'"):
    break
else:
    chars.append(ch)
```

Alternatif ini tidak digunakan karena `_peek()` untuk mencocokkan dan `_advance()` untuk
mengonsumsi digunakan secara eksplisit sehingga penelusuran kode lebih mudah dipahami.

**Test regresi.** `test_dua_kutip_berturut_turut` di `tests/test_tambahan.py`.

**Peran AI.** Hana: ya, AI membantu memperbaiki bug ini dengan menelusuri kode percobaan,
membantu mengambil keputusan antara `_peek()` dan `_advance()`, memeriksa test, dan menjelaskan
cara melihat output. Diverifikasi dengan menjalankan kode dan membandingkan hasilnya berdasarkan
penjelasan yang diberikan AI. Upi: AI membantu memahami dan mereviu perbaikan ini; diverifikasi
dengan `pytest` dan kasus tepi (string kosong dan satu karakter kutip).

---

## Bug 3: `<>` terbaca sebagai `<` dan `>` (operator terpotong)

**Ditemukan oleh:** Hana Mardhiyyah (juga terlihat dari test terlihat `test_matrix_laporan_penjualan` yang gagal) · **Diperbaiki oleh:** Hana Mardhiyyah (commit `47abc33`)

**Gejala.** Input: `<> <= >=`.
Output yang didapat: `[Token(OP, '<', 1:1), Token(OP, '>', 1:2), Token(OP, '<=', 1:4), Token(OP, '>=', 1:7), Token(EOF, '', 1:9)]`.
Output yang diharapkan: `[Token(OP, '<>', 1:1), Token(OP, '<=', 1:4), Token(OP, '>=', 1:7), Token(EOF, '', 1:9)]`
(SPESIFIKASI.md bagian 2.5). Dampaknya terlihat di `data/sample/laporan_penjualan.sql`: parser
melaporkan "Baris 6, kolom 41: diharapkan ekspresi, ditemukan '>'".

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT a FROM t WHERE x <> 1
```

**Akar masalah.** Kode lama salah karena tidak mencocokkan apakah karakter selanjutnya adalah `>`.
Sehingga, jika tidak cocok dengan tanda `=`, maka karakter akan langsung memutuskan untuk
mengambil karakter `<`. Kode tidak menerapkan lookahead dan maximal munch pada Bab 4: Scanning.
Lookahead adalah proses mencocokkan karakter selanjutnya. Lookahead akan mencocokkan karakter
selanjutnya untuk memutuskan apakah tanda `<` tersebut menandakan karakter `<>` atau `<`. Maximal
munch adalah karakter yang terpanjang yang akan diambil, sehingga pada kasus ini, karakter yang
diambil adalah `<>`.

**Perbaikan.** File yang diubah: `lexer.py`. Fungsi yang diubah: `_scan_token`.
Alasan: karena maximal munch merupakan bagian dari scanning. Scanning mengubah data mentah menjadi
nilai yang akan diproses. Sehingga, file yang diubah adalah `lexer.py`. Fungsi `_scan_token`
diubah karena fungsi tersebut memproses lexeme operator yang diawali dengan `<`.

Perbaikan alternatif:

```python
elif self._peek() == '>':
    self._advance()
    op = "<>"
```

Alternatif ini tidak digunakan karena mengikuti pola sebelumnya, yaitu `<=` yang menggunakan
`_match`.

**Test regresi.** `test_operator_terpanjang` di `tests/test_tambahan.py`.

**Peran AI.** Hana: tidak, karena bug ini hanya menambahkan tanda `>` dan `<=` memiliki pola yang
sama untuk diterapkan ke `<>`, sehingga tidak menggunakan AI untuk bug ini. Upi: AI membantu
memetakan gejala `test_matrix_laporan_penjualan` ke penyebabnya (`<>`) dan memahami perbaikan;
diverifikasi dengan `pytest` dan `evaluate.py`.

---

## Bug 4: Pemulihan error (panic mode) membuang semua statement sesudahnya

**Ditemukan oleh:** Hana Mardhiyyah · **Diperbaiki oleh:** Hana Mardhiyyah (commit `fb8f33d`)

**Gejala.** Input: `SELECT id FROM ;` diikuti baris baru lalu `SELECT nama FROM pelanggan;`.
Output yang didapat: `[]` (tidak ada statement yang terbaca).
Output yang diharapkan: `[Select(distinct=False, columns=[SelectItem(expr=ColumnRef(qualifier=None, name='nama', line=2), alias=None)], sources=[TableRef(name='pelanggan', alias=None, line=2)], joins=[], where=None, group_by=[], order_by=[], line=2)]`
(SPESIFIKASI.md bagian 5 dan 6).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT id FROM ;
SELECT nama FROM pelanggan;
```

**Akar masalah.** Ketika parser mendeteksi error, parser memasuki panic mode ketika terdapat
minimal satu token yang tidak masuk akal dalam suatu kondisi di tengah produksi grammar. Ketika
akan kembali parsing, parser perlu menyelaraskan status urutan token yang akan datang sehingga
token berikutnya sesuai dengan aturan yang sedang di-parse. Proses ini disebut sinkronisasi. Pada
kode lama, ketika parser mendeteksi error dan memasuki panic mode, tidak melakukan sinkronisasi
dengan benar; fungsi `_synchronize` membuang token sampai akhir input dan tidak berhenti di `;`.
Sehingga, token berikutnya yang sesuai dengan aturan ikut terbuang dan tidak terbaca. Kode tidak
menerapkan sinkronisasi pada Bab 6: Parsing Expressions.

**Perbaikan.** File yang diubah: `parser.py`. Fungsi yang diubah: `_synchronize`.
Alasan: karena sinkronisasi merupakan bagian dari parser. Parser menyusun token menjadi grammar
sesuai aturan yang berlaku. Sehingga, file yang diubah adalah `parser.py`. Fungsi `_synchronize`
diubah karena fungsi tersebut membuang atau mengambil karakter ketika terjadi `ParseError`.

Perbaikan alternatif:

```python
while (True):
  if not self._at_end() and not self._match(T.SEMICOLON):
    self._advance()
  else:
    break
```

Alternatif ini tidak digunakan karena kode menjadi lebih panjang dan tidak efisien.

**Test regresi.** `test_hanya_statement_gagal_yang_dibuang` di `tests/test_tambahan.py`.

**Peran AI.** Hana: ya, AI membantu menemukan dan memperbaiki bug. AI menunjukkan lokasi dan
memandu analisis kondisi loop. Diverifikasi dengan menjalankan test yang merah di kode lama lalu
hijau setelah perbaikan. Upi: AI membantu memahami dan mereviu perbaikan ini; diverifikasi dengan
`pytest` dan kasus tepi (error di tengah statement).

---

## Bug 5: `LEFT OUTER JOIN` ditolak

**Ditemukan oleh:** Hana Mardhiyyah · **Diperbaiki oleh:** Hana Mardhiyyah (commit `ce8dd29`)

**Gejala.** Input: `SELECT a.id FROM a LEFT OUTER JOIN b ON b.a_id = a.id`.
Output yang didapat: `AssertionError: [ParseError("Baris 1, kolom 25: diharapkan JOIN, ditemukan 'OUTER'")]`.
Output yang diharapkan: `[Join(kind='LEFT', source=TableRef(name='b', alias=None, line=1), condition=BinaryOp(left=ColumnRef(qualifier='b', name='a_id', line=1), op='=', right=ColumnRef(qualifier='a', name='id', line=1)), line=1)]`
(SPESIFIKASI.md bagian 3).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT a.id FROM a LEFT OUTER JOIN b ON b.a_id = a.id
```

**Akar masalah.** Kode lama salah karena pada SPESIFIKASI.md, `LEFT` dapat digunakan dengan `OUTER`
sebelum `JOIN`. `OUTER` bersifat opsional. Pada kode, `OUTER` belum diterapkan sehingga kode
langsung mengharapkan `JOIN`. Kode tidak menerapkan konsep menerjemahkan grammar ke kode pada
Bab 6: Parsing Expressions. Pada kode, seharusnya `OUTER` diletakkan setelah ekspresi `LEFT` untuk
dicocokkan. Namun, pada kode lama hal ini tidak diterapkan dan `OUTER` belum diterjemahkan dari
grammar menjadi kode.

**Perbaikan.** File yang diubah: `parser.py`. Fungsi yang diubah: `_join`.
Alasan: karena join merupakan salah satu aturan grammar, sehingga bagian dari parser. Parser
menyusun token menjadi grammar sesuai aturan yang berlaku. Sehingga, file yang diubah adalah
`parser.py`. Fungsi `_join` diubah karena fungsi tersebut mengatur grammar join yang mengatur
`LEFT` dan `OUTER`.

Perbaikan alternatif:

```python
elif self._match_kw("LEFT"):
    if self._check_kw("OUTER"):
        self._advance()
    kind = "LEFT"
```

Alternatif ini tidak digunakan karena kode menjadi lebih panjang dan tidak efisien.

**Test regresi.** `test_left_outer_join` di `tests/test_tambahan.py`.

**Peran AI.** Hana: ya, AI mengarahkan pemeriksaan `_join()` terhadap grammar dan menunjukkan
bahwa `OUTER` tidak punya baris kode. Diverifikasi dengan menjalankan test yang merah di kode lama
(diharapkan JOIN, ditemukan 'OUTER') lalu hijau setelah perbaikan. Upi: AI membantu memahami dan
mereviu perbaikan ini; diverifikasi dengan `pytest`.

---

## Bug 6: `AND` dan `OR` diperlakukan setingkat (precedence)

**Ditemukan oleh:** Hana Mardhiyyah · **Diperbaiki oleh:** Hana Mardhiyyah (commit `d88064c`)

**Gejala.** Input: `SELECT a FROM t WHERE x = 1 OR y = 2 AND z = 3`.
Output yang didapat: `BinaryOp(left=BinaryOp(left=BinaryOp(left=ColumnRef(qualifier=None, name='x', line=1), op='=', right=Literal(value='1', kind='number')), op='OR', right=BinaryOp(left=ColumnRef(qualifier=None, name='y', line=1), op='=', right=Literal(value='2', kind='number'))), op='AND', right=BinaryOp(left=ColumnRef(qualifier=None, name='z', line=1), op='=', right=Literal(value='3', kind='number')))`,
yaitu `(x = 1 OR y = 2) AND z = 3`.
Output yang diharapkan: `BinaryOp(left=BinaryOp(left=ColumnRef(qualifier=None, name='x', line=1), op='=', right=Literal(value='1', kind='number')), op='OR', right=BinaryOp(left=BinaryOp(left=ColumnRef(qualifier=None, name='y', line=1), op='=', right=Literal(value='2', kind='number')), op='AND', right=BinaryOp(left=ColumnRef(qualifier=None, name='z', line=1), op='=', right=Literal(value='3', kind='number'))))`,
yaitu `x = 1 OR (y = 2 AND z = 3)` (SPESIFIKASI.md bagian 3.1).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT a FROM t WHERE x = 1 OR y = 2 AND z = 3
```

**Akar masalah.** Kode lama salah karena `AND` harus didahulukan daripada `OR` walaupun `OR`
berada paling kiri dibandingkan `AND`. Konsep yang dilanggar adalah precedence pada Bab 6:
Parsing Expressions.

**Perbaikan.** File yang diubah: `parser.py`. Fungsi yang diubah: `_logical` dan `_expr`.
Alasan: karena `_logical` dan `_expr` merupakan bagian dari grammar, sehingga bagian dari parser.
Parser menyusun token menjadi grammar sesuai aturan yang berlaku. Sehingga, file yang diubah
adalah `parser.py`. Fungsi `_logical` diubah menjadi `_and` dan `_or` karena fungsi tersebut
mengatur ekspresi `AND` dan `OR`, tetapi tidak memperhatikan precedence. `_expr` diubah menjadi
memanggil `_or` karena `_and` sudah dipanggil di dalam `_or` untuk dibandingkan mana yang
didahulukan.

Perbaikan alternatif:

```python
def _expr(self):
    return self._logical()

def _logical(self, level=0):
    # level 0 = OR, level 1 = AND, level 2 = tingkat terdalam (_not)
    operators = [("OR",), ("AND",)]
    if level == 2:
        return self._not()
    left = self._logical(level + 1)
    while self._check_kw(*operators[level]):
        op = self._advance().value
        left = ast.BinaryOp(left, op, self._logical(level + 1))
    return left
```

Alternatif ini tidak digunakan karena kodenya lebih sulit dicocokkan baris demi baris dengan
grammar.

**Test regresi.** `test_and_didahulukan_dari_or` di `tests/test_tambahan.py`.

**Peran AI.** Hana: ya. AI menunjukkan bahwa `_logical` perlu dicocokkan dengan grammar `or_expr`
dan `and_expr`, serta memandu perancangan test (input yang membedakan dua pohon, ekspektasi dari
grammar). AI juga menunjuk bahwa `_and` belum dipanggil oleh `_or` dan bahwa `_expr` harus
memanggil tingkat paling luar. Upi: AI membantu memahami dan mereviu perbaikan ini; diverifikasi
dengan `pytest` dan satu kasus tepi (`NOT`, `AND`, `OR` bersama).

---

## Bug 7: Urutan pencarian alias scope terbalik

**Ditemukan oleh:** Upi, melalui pemeriksaan kode terhadap spesifikasi dengan bantuan AI · **Diperbaiki oleh:** Upi (draf perbaikan dibantu AI)

**Gejala.** Input: subquery memakai alias `x` yang sama dengan alias di query luar. Output yang
didapat: kolom `x.id` di dalam subquery di-resolve ke tabel `a` (tabel query luar). Output yang
diharapkan: `b` (tabel di subquery), karena qualifier dicari dari scope terdalam ke luar dan yang
pertama ditemukan dipakai (SPESIFIKASI.md bagian 4.3, *shadowing*). Pola ini ada di
`data/sample/audit.sql` baris 12-14.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT 1 FROM a x WHERE EXISTS (SELECT 1 FROM b x WHERE x.id = 1)
```

**Akar masalah.** Fungsi `_lookup` mengumpulkan rantai scope dari terdalam ke terluar, lalu
membaliknya sebelum mencari. Akibatnya scope terluar diperiksa lebih dulu, padahal aturan
*shadowing* meminta pencarian dimulai dari scope terdalam dan berhenti pada yang pertama
ditemukan. Alias di subquery pun terikat ke tabel luar. Rujukan: Bab 11, *Resolving Variable
Expressions* (pencarian nama dimulai dari scope paling dalam).

**Perbaikan.** `crud/resolver.py`, fungsi `_lookup`: pencarian berjalan dari `self.scope` ke
induknya satu per satu dan berhenti pada nama pertama yang ditemukan; langkah `reversed(chain)`
dihapus. Alternatif: tetap membuat daftar rantai lalu mengulang tanpa dibalik. Hasilnya sama,
tetapi dipilih perulangan langsung karena tidak perlu daftar perantara.

**Test regresi.** `test_alias_subquery_menutupi_alias_luar` di `tests/test_tambahan.py`.

**Peran AI.** AI memeriksa `resolver.py` terhadap spesifikasi dan mengusulkan perbaikan. Kami
menerapkannya dan memverifikasi: test regresi gagal sebelum perbaikan (`'a' != 'b'`) dan lulus
sesudahnya; seluruh test (47) lulus.

---

## Bug 8: Scope `DELETE` tidak ditutup sehingga alias bocor

**Ditemukan oleh:** Upi, melalui pemeriksaan kode terhadap spesifikasi dengan bantuan AI · **Diperbaiki oleh:** Upi (draf perbaikan dibantu AI)

**Gejala.** Input: `DELETE` ber-alias `z`, lalu `SELECT` yang memakai `z.id` padahal `z` bukan
tabel di `SELECT` itu. Output yang didapat: `z.id` di-resolve ke tabel `a` dan tidak ada
diagnostik. Output yang diharapkan: error `alias 'z' tidak terdefinisi`, karena tiap statement
berdiri sendiri dan tidak boleh ada scope tersisa (SPESIFIKASI.md bagian 4.5). Pola ini ada di
`data/sample/audit.sql` baris 16-18 (alias `s`).

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
DELETE FROM a z;
SELECT z.id FROM b;
```

**Akar masalah.** Resolver membuka scope baru dengan `_push()` untuk setiap statement, tetapi
`_delete` tidak menutupnya dengan `_pop()`. Scope itu tertinggal dan menjadi induk bagi statement
berikutnya, sehingga alias `DELETE` terlihat oleh `SELECT` sesudahnya. Prinsipnya sama dengan
pasangan `beginScope` dan `endScope` di buku: membuka dan menutup scope harus berpasangan.
Rujukan: Bab 11, *Resolving Blocks*.

**Perbaikan.** `crud/resolver.py`, fungsi `_delete`: ditambahkan `self._pop()` di akhir,
berpasangan dengan `self._push()` di awal. Alternatif: mengosongkan `self.scope` setiap statement
selesai di `resolve_script`. Tidak dipilih karena itu menutupi pelanggaran pasangan push/pop di
fungsi lain; perbaikan ditempatkan di sumber masalahnya.

**Test regresi.** `test_scope_tidak_bocor_antar_statement` di `tests/test_tambahan.py`.

**Peran AI.** AI memeriksa `resolver.py` terhadap spesifikasi dan mengusulkan perbaikan. Kami
menerapkannya dan memverifikasi: test regresi gagal sebelum perbaikan (`'a' is None`) dan lulus
sesudahnya; 47 test lulus.

---

## Bug 9: Tabel di subquery `UPDATE` dihitung U, seharusnya R

**Ditemukan oleh:** Upi (gejala dari `evaluate.py` dan `test_matrix_laporan_penjualan`), penyebab ditelusuri dengan bantuan AI · **Diperbaiki oleh:** Upi (draf perbaikan dibantu AI)

**Gejala.** Input: `UPDATE` dengan subquery di `WHERE` atau `SET`. Output yang didapat: tabel di
subquery mendapat operasi `U`. Output yang diharapkan: `R`, karena membaca tabel lewat subquery
selalu R apa pun jenis statement luarnya (SPESIFIKASI.md bagian 5). Terlihat dari
`python evaluate.py`: `('laporan_penjualan.sql', 12, 'pesanan', 'U')` salah ditemukan dan
`('laporan_penjualan.sql', 12, 'pesanan', 'R')` terlewat; `test_matrix_laporan_penjualan` juga
menghasilkan `pesanan: RUD` padahal seharusnya `RD`.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
UPDATE a SET x = 1 WHERE id IN (SELECT id FROM b)
```

**Akar masalah.** Fungsi `_collect` menandai tabel di dalam subquery dengan operasi yang
diberikan pemanggilnya. Cabang `Update` memberi `"U"`, sehingga tabel yang hanya dibaca ikut
dianggap diubah. Aturan lokal proyek menyatakan membaca lewat subquery selalu R dan hanya tabel
target `UPDATE` yang U. Cabang `Delete` sudah benar karena memberi `"R"`. Ini aturan semantik
tahap analisis di atas AST (spesifikasi bagian 7), dan tidak ada bab di *Crafting Interpreters*
yang membahas aturan CRUD proyek ini.

**Perbaikan.** `crud/analyzer.py`, fungsi `analyze_statement`, cabang `Update`: pemanggilan
`_collect` untuk nilai `SET` dan untuk `WHERE` memakai `"R"`, bukan `"U"`; hanya tabel target
yang tetap `U`. Alternatif: mengubah `_collect` agar selalu memakai `"R"` untuk subquery. Tidak
dipilih karena `_collect` dipakai juga oleh cabang lain, dan perubahan dua argumen di cabang
`Update` lebih kecil risikonya.

**Test regresi.** `test_subquery_di_update_dibaca_R` di `tests/test_tambahan.py`.

**Peran AI.** AI membantu menelusuri penyebab dari keluaran `evaluate.py` dan mengusulkan
perbaikan. Kami menerapkannya dan memverifikasi: test regresi gagal sebelum perbaikan dan lulus
sesudahnya; `test_matrix_laporan_penjualan` kini lulus; `evaluate.py` menunjukkan parser F1 1.00.

---

## Bagian yang dilengkapi (TODO)

- **T3, komentar blok** (`crud/lexer.py`, commit `32ffa6e` dan `6669946` oleh Hana Mardhiyyah): komentar
  `/* ... */` dipindai sampai `*/`; bila input habis sebelum itu, dilempar `LexError` "komentar
  blok tidak ditutup" dengan posisi awal komentar. Spesifikasi 2.3. Test:
  `test_komentar_blok_tidak_ditutup_adalah_lexerror` dan kasus tepi `test_tepi_komentar_blok_kosong`.
- **T1, `INSERT ... SELECT`** (`crud/parser.py`, commit `84cd8ae` oleh Hana Mardhiyyah): bagian `SELECT`
  diparse dengan `_select()` dan dibungkus dalam node `Insert`. Spesifikasi 3 dan 5. Test:
  `test_insert_select_matrix`.
- **T2, resolusi kolom tanpa qualifier** (`crud/resolver.py`, fungsi `_column`, oleh Upi): hanya
  scope terdalam yang dilihat. Satu tabel di scope itu: `ColumnRef.resolved` diisi tabelnya. Lebih
  dari satu tabel: warning `kolom 'x' ambigu tanpa skema` dan `resolved` tetap `None`. Tidak ada
  tabel (misalnya kolom di `INSERT ... VALUES`): warning. Spesifikasi 4.3. Test:
  `test_kolom_tanpa_qualifier_satu_tabel_dan_ambigu`. Keterbatasan: kolom milik tabel luar pada
  subquery berkorelasi tidak ikut di-resolve bila ditulis tanpa qualifier.