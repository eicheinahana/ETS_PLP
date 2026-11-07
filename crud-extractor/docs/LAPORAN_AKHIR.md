# Laporan Akhir

Kelompok: 251524011 - Hana Mardhiyyah dan 251524020 - Luthfiah Nurazizah

## 1. Hasil evaluasi

Keluaran `python evaluate.py` dijalankan setelah `data/ground_truth.csv` memuat label manual untuk
keempat file contoh (label ditulis dari SPESIFIKASI.md bagian 5, bukan disalin dari output tool).

Evaluasi pertama menunjukkan parser dan regex sama-sama berbeda dari label pada `audit.sql` baris 20.
Dua metode yang cara kerjanya sangat berbeda menghasilkan jawaban yang sama, sehingga kami mencurigai label.
Setelah membaca ulang SPEC bagian 5, ternyata label kami tertukar: pada `UPDATE pesanan ... WHERE pelanggan_id IN
(SELECT id FROM pelanggan ...)`, tabel `pesanan` adalah target (U) dan `pelanggan` hanya dibaca lewat subquery (R).
Dua baris label dikoreksi, lalu evaluasi dijalankan ulang.

```text
Dievaluasi: audit.sql, campuran_error.sql, laporan_penjualan.sql, pemeliharaan.sql (27 triple)

Metode   Precision  Recall     F1
parser        1.00    1.00   1.00
regex         0.65    0.81   0.72

[parser]

[regex]
  salah ditemukan (FP): ('audit.sql', 16, 'sesi', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 4, 'pesanan', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 8, 'keranjang', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'D')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pesanan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'rahasia', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 15, 'pesanan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.alamat', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.pelanggan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'pelanggan_lama', 'U')
  salah ditemukan (FP): ('pemeliharaan.sql', 15, 'crm.alamat', 'R')
  terlewat (FN):       ('audit.sql', 2, 'pesanan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pelanggan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pesanan', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.alamat', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.pelanggan', 'R')
```

Dari 27 triple label, parser menemukan seluruhnya dengan benar tanpa temuan salah dan tanpa yang terlewat
(precision, recall, dan F1 masing-masing 1,00). Regex menemukan 22 triple dengan benar, menghasilkan 12 temuan
salah (FP) dan melewatkan 5 (FN), sehingga precision 0,65, recall 0,81, dan F1 0,72. Precision regex paling
rendah karena ia melaporkan tabel yang tidak pernah dieksekusi: teks di komentar atau string, tabel target
`DELETE` yang ikut dihitung R, dan statement yang gagal di-parse (bagian 2). Recall regex lebih tinggi
daripada precision-nya karena regex cenderung melaporkan terlalu banyak, bukan terlalu sedikit.

## 2. Tiga kasus di mana regex salah

1. **Teks di komentar dan di dalam string dihitung sebagai SQL.**
   ```sql
   -- DELETE FROM pelanggan   (baris ini komentar, bukan perintah)
   SELECT p.nama, SUM(o.total) AS omzet
   ...
   WHERE o.status = 'LUNAS' AND o.catatan <> 'FROM rahasia'
   ```
   (`laporan_penjualan.sql` baris 2 dan 6). Regex melaporkan `pelanggan` D (dari komentar) dan `rahasia` R
   (dari isi string). Hal yang sama terjadi di `pemeliharaan.sql` baris 2: kalimat dalam komentar blok
   `UPDATE pelanggan_lama` terbaca sebagai `pelanggan_lama` U. Karena komentar ikut menjadi bagian dari
   potongan statement, baris statement juga tercatat salah (regex melapor di baris 2, seharusnya baris 3),
   sehingga muncul FP di baris 2 dan FN di baris 3. Parser benar karena lexer (Bab 4) membuang komentar
   sebelum token dibentuk dan membaca isi `'FROM rahasia'` sebagai satu token `STRING`. Baris yang dicatat
   adalah baris keyword awal statement (SPEC 8).

2. **Tabel target `DELETE` ikut dihitung R.**
   ```sql
   DELETE FROM pesanan WHERE tanggal < :batas;
   ```
   (`laporan_penjualan.sql` baris 15; kasus serupa di `audit.sql` baris 16 `sesi`, `pemeliharaan.sql` baris 15
   `crm.alamat`, dan `campuran_error.sql` baris 8 `keranjang`). Regex memperlakukan setiap `FROM x` sebagai
   pembacaan (R), sehingga tabel yang dihapus tercatat D dan R sekaligus. Menurut SPEC 5, `DELETE` hanya
   memberi D pada tabel target. Parser benar karena operasi ditentukan oleh jenis statement pada pohon
   (Bab 5 dan 6): target `delete_stmt` mendapat D, dan R hanya untuk tabel di subquery atau sumber `SELECT`.
   Regex juga melewatkan tabel kedua pada daftar `FROM` bertanda koma
   (`FROM pelanggan p, pesanan o` di `audit.sql` baris 2, sehingga `pesanan` R terlewat).

3. **Statement yang gagal di-parse tetap dihitung.**
   ```sql
   SELECT id nama, FROM pesanan;
   ```
   (`campuran_error.sql` baris 4). Regex melaporkan `pesanan` R padahal statement ini salah sintaks (ada
   koma sebelum `FROM`). Menurut SPEC 5, statement yang gagal di-parse tidak dihitung. Regex tidak punya
   gagasan "statement valid". Parser mendeteksi error, melaporkannya sekali, dan membuang token sampai `;`
   (panic mode, Bab 6), sehingga statement valid sesudahnya (`UPDATE produk` dan `DELETE FROM keranjang`)
   tetap diproses dan statement rusak tidak masuk ke matrix.

## 3. Batas pendekatan kami

1. **Kolom tanpa qualifier pada lebih dari satu tabel tidak bisa dipetakan.**
   ```sql
   SELECT nama FROM pelanggan, pemasok;
   ```
   Akibat: tool hanya mengeluarkan warning `kolom 'nama' ambigu tanpa skema` dan `resolved = None`;
   penggunaan kolom (`--kolom`) tidak bisa dikaitkan ke tabel mana pun. CRUD matrix tingkat tabel tetap
   benar karena kedua tabel tetap R. Informasi yang dibutuhkan: skema database (daftar kolom per tabel).

2. **Konstruksi SQL di luar lingkup spesifikasi tidak diproses.**
   ```sql
   WITH aktif AS (SELECT * FROM pelanggan) SELECT * FROM aktif
   UNION SELECT * FROM pemasok;
   ```
   Akibat: `WITH` dan `UNION` menimbulkan error sintaks; statement tidak dihitung sehingga `pelanggan`
   dan `pemasok` hilang dari matrix (recall turun). Hal yang sama berlaku untuk `MERGE`, DDL, quoted
   identifier, dan `t.*`. Yang dibutuhkan: perluasan grammar dan aturan resolver (nama CTE bukan tabel nyata).

3. **SQL dinamis, view, trigger, dan stored procedure tidak terlihat dari teks query.**
   ```sql
   -- aplikasi merakit: "DELETE FROM " + nama_tabel
   SELECT * FROM v_pelanggan_aktif;
   ```
   Akibat: tabel yang dipilih saat runtime tidak muncul; `v_pelanggan_aktif` dicatat sebagai tabel padahal
   merupakan view atas beberapa tabel, dan operasi di dalam trigger tidak terhitung. Informasi yang
   dibutuhkan: kode aplikasi pemanggil (analisis aliran data) atau katalog database (definisi view dan trigger).

Catatan tambahan: aturan CRUD proyek bersifat lokal (misalnya `INSERT` target selalu C, subquery selalu R)
dan hasil per file adalah gabungan seluruh statement tanpa memperhatikan urutan atau kondisi eksekusi.

## 4. Pembagian kerja

Kami bekerja secara pair programming (bergantian driver dan navigator), bukan membagi modul.

| Bagian | Driver utama | Navigator |
| --- | --- | --- |
| Lexer: kutip `''`, `<>`, komentar blok (T3) | Hana | Luthfiah |
| Parser: `_synchronize`, `OUTER`, presedensi `AND`/`OR`, `INSERT ... SELECT` (T1) | Hana | Luthfiah |
| Resolver (T2): kolom tanpa qualifier, pencarian scope, scope `DELETE`, scope antar statement | Luthfiah | Hana |
| Analyzer (subquery di `UPDATE` tetap R), ground truth, `evaluate.py` | Luthfiah | Hana |
| Test tambahan dan dokumen (laporan bug, kartu desain, laporan akhir, log AI) | Luthfiah dan Hana | Luthfiah dan Hana |

Untuk memastikan keduanya memahami seluruh kode, kami bergantian menjelaskan perbaikan satu sama lain
tanpa melihat kode, saling memprediksi keluaran `--ast`, dan saling menguji akar masalah tiap bug secara
lisan sebelum demo.
