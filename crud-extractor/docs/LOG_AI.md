# Log Penggunaan AI

Catat setiap penggunaan AI atau coding agent yang memengaruhi kode atau laporan.

| No | Siapa | Prompt / tugas (ringkas) | Hasil: diterima, diubah, atau ditolak | Alasan | Cara verifikasi |
| --- | --- | --- | --- | --- | --- |
| 1 | Upi | Meminta penjelasan isi dokumen tugas: tujuan, bobot nilai, dan alur pengerjaan | Diterima sebagian | Membantu memahami gambaran besar; acuan tetap dokumen tugas dan SPESIFIKASI.md | Dicocokkan dengan dokumen tugas dan spesifikasi |
| 2 | Upi | Meminta penjelasan konsep dengan analogi: API publik, tanpa skema database, test regresi vs kasus tepi, kartu desain | Diterima | Membantu memahami sebelum mengerjakan | Dicocokkan dengan spesifikasi dan templat laporan; jawaban pemahaman saya dikoreksi AI |
| 3 | Upi | Membantu membaca hasil `pytest` awal (5 gagal) dan memetakan gejala ke bagian tugas | Diubah | Dugaan sumber gejala saya cek ulang, tidak diambil mentah | Dicocokkan dengan keluaran `pytest`, spesifikasi, dan kode |
| 4 | Upi | Meminta penyelesaian T2 dan bug resolver/analyzer (bug 7, 8, 9) beserta penjelasan | Diterima setelah diverifikasi | Waktu terbatas; penyebabnya dijelaskan sehingga bisa saya pahami | Test regresi gagal sebelum dan lulus sesudah perbaikan; 47 test lulus |
| 5 | Upi | Meminta test regresi dan 5 test kasus tepi | Diterima | Mengikuti format test yang sudah ada | Dijalankan pada kode lama dan kode baru |
| 6 | Upi | Meminta label ground truth `audit.sql` dan `pemeliharaan.sql` beserta alasan per statement | Diterima setelah dicek | Waktu terbatas; alasan per statement dijelaskan | Dicocokkan per statement dengan spesifikasi bagian 5 dan `evaluate.py` (parser F1 1.00) |

**Refleksi (3-5 kalimat).** 

AI paling membantu untuk memetakan alur pipeline, menjelaskan konsep
dengan analogi, dan memeriksa kode terhadap spesifikasi sehingga bug di resolver dan analyzer
ketemu dengan cepat. 

|1|Hana|Bertanya apakah `\\\_peek` bisa dibuat mundur (lookbehind)|Diterima sebagai pemahaman, kode tidak diubah|AI menjelaskan indeks negatif Python membaca dari belakang string tanpa error, dan lexer Bab 4 hanya butuh lookahead|Penelusuran manual nilai `pos` dan `offset`|
|2|Hana|Memeriksa aturan keyword tidak peka huruf besar/kecil di `\\\_word`|Diterima, kode tidak diubah|AI memandu penelusuran `Select`, `selectx`, `my\\\_table`, dan menyebut risiko Unicode pada `isalnum()`/`upper()`|Penelusuran manual. Perilaku Unicode tidak diklaim sebagai bug karena spesifikasi tidak menyebutnya|
|3|Hana|Menanyakan arti test regresi, red-green-refactor, dan "5 test kasus tepi"|Diterima|AI menjelaskan konsep dan menyarankan menulis sendiri 5 kasus tepi karena `test\\\_tambahan.py` kosong|Mencocokkan dengan docstring `test\\\_tambahan.py`|
|4|Hana|Melengkapi komentar blok `/\\\* ... \\\*/` di lexer (TODO T3)|Diubah: kode ditulis sendiri, AI memandu lewat pertanyaan dan menunjuk kesalahan kondisi `while`, `\\\_match` yang punya efek samping, jumlah `\\\_advance()`, dan `raise` tak terjangkau|AI menunjukkan letak masalah, perbaikan ditulis sendiri|Penelusuran manual `/\\\* a \\\*/`, `/\\\*\\\*/`, `/\\\* a`, `/\\\* a \\\*/x`|
|5|Hana|Memperbaiki kutip ganda `''` di `\\\_string()`|Diubah: versi awal ditolak, versi akhir `if/elif` ditulis sendiri|AI menunjukkan dua `if` terpisah membuat kutip kedua dinilai ulang sebagai penutup. Sempat keliru menyatakan hasil kode saya bukan `O'Brien`|Menjalankan `print(tokenize(...))` di kode lama (token `O` dan `Brien`) dan kode baru. Test `test\\\_dua\\\_kutip\\\_berturut\\\_turut` merah lalu hijau|
|6|Hana|Menulis dan men-debug `tests/test\\\_tambahan.py` (nama `test\\\_`, `pytest.raises`, `print` dengan `-s`, perbedaan `Script` dan node)|Diterima|AI menunjukkan salah nama fungsi, salah ketik `statement`, `assert` hilang, dan ekspektasi yang disalin dari output kode|Menjalankan pytest|
|7|Hana|Melengkapi `INSERT ... SELECT` di parser (TODO T1)|Diubah: kode ditulis sendiri|AI memandu: `\\\_value\\\_row()` salah dipanggil di cabang `SELECT`, `values` harus `\\\[]`, bukan `None` atau `list`|`test\\\_insert\\\_select` dan `test\\\_insert\\\_values` milik dosen hijau. Sempat salah ubah `rows.append(self.\\\_table\\\_ref())`, ketahuan lewat test merah dan dikembalikan|
|8|Hana|Bug `\\\_synchronize` (panic mode)|Diubah|AI menunjuk lokasi bug (membuang token sampai EOF) dan memandu kondisi `while` lewat De Morgan. Sempat keliru mengira test dijalankan di kode baru, saya koreksi|Test `test\\\_hanya\\\_statement\\\_gagal\\\_yang\\\_dibuang` merah di kode lama, hijau setelah perbaikan|
|9|Hana|Test kasus tepi error lalu EOF tanpa `;`|Diterima dengan koreksi|AI menyebut test ini bukan regresi karena lulus di kode lama juga, dan menjaga agar `\\\_synchronize` tidak hang|Penelusuran manual di EOF, test hijau|
|10|Hana|Memeriksa `join` terhadap grammar|Diubah|AI menunjuk bahwa `OUTER` tidak punya baris kode di `\\\_join()`. Perbaikan `\\\_match\\\_kw("OUTER")` ditulis sendiri|`test\\\_left\\\_outer\\\_join` merah (`diharapkan JOIN, ditemukan 'OUTER'`, kolom 25), hijau setelah perbaikan. `test\\\_left\\\_join` dosen tetap lulus|
|11|Hana|Bug presedensi `AND`/`OR` di `\\\_logical`|Diubah|AI menunjukkan `\\\_logical` menyamakan `AND` dan `OR`. `\\\_or`, `\\\_and`, dan `\\\_expr` ditulis sendiri|`test\\\_and\\\_didahulukan\\\_dari\\\_or` merah (akar `AND`), hijau setelah perbaikan. Test dosen lulus|
|12|Hana|Merangkum Bab 4 dan Bab 6 Crafting Interpreters|Diterima dengan koreksi|AI sempat memakai notasi `\\\[ ]` seolah milik buku, padahal buku memakai `?` dan `\\\[ ]` milik spesifikasi|Membandingkan dengan isi bab dan grammar di spesifikasi|
|13|Hana|Memeriksa dan merevisi draf Laporan Bug|Diubah|AI menunjuk kesalahan (konsep keliru, alasan menolak alternatif tidak benar, reproduksi minimal bukan statement valid). Teks laporan ditulis sendiri|Membandingkan draf dengan output nyata dan isi chat|

**Refleksi (3-5 kalimat).** Di bagian mana AI paling membantu? Di mana AI keliru atau
menyesatkan, dan bagaimana kalian mengetahuinya?

AI paling membantu dalam menunjuk letak masalah lewat penelusuran nilai langkah demi langkah dan mencocokkan fungsi parser dengan grammar, sehingga saya bisa menulis perbaikan sendiri. AI juga beberapa kali keliru: menyatakan hasil kode `\\\_string()` saya salah padahal benar (`O'Brien`), mengira test dijalankan di kode baru padahal sudah merah di kode lama, dan memakai notasi `\\\[ ]` seolah milik buku. Kekeliruan itu ketahuan karena saya menjalankan kode dan membandingkan hasilnya, bukan hanya mengikuti penjelasan AI.