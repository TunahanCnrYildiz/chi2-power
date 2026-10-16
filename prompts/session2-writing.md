# Oturum 2 · Yazım — ilk prompt (TASLAK)

> Bu prompt SPEC.md tamamlanınca kesinleşecek.
> Temiz oda: bu oturum **ayrı bir klasörde** (ya da yalnızca SPEC.md, CONTRACT.md ve oracle/ kopyalanmış temiz bir klonda) başlatılır.
> LEDGER.md, `re-work/` ve Ghidra/REA çıktıları bu oturuma verilmez.

Ajan: _TODO_
Tarih: _TODO_

---

Sana yalnızca bir davranış belgesi (`SPEC.md`) ve bir CLI sözleşmesi (`CONTRACT.md`) veriyorum. Bu belgelere göre χ² olumsallık tablosu güç analizini yapan bir hesap motoru ve CLI yaz.

- Dil: _TODO_
- CLI adı: `gpower-clone`; çıktı tek satır JSON, geçersiz girdide `{"error": "..."}` ve sıfırdan farklı çıkış kodu.
- Önce SPEC'teki kabul kriterlerini ve `oracle/vectors.csv`'yi test olarak yaz, sonra motoru yaz.
- SPEC'te olmayan bir davranış gerekiyorsa uydurma: soru olarak raporla.
