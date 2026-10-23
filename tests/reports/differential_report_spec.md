# Diferansiyel test raporu (G*Power kâhini ↔ gpower-clone, sözleşme v1.0.0)

- Kaynak: `tests/fixtures/spec_vectors.csv`
- Toplam vektör: **30** (20 hesap, 7 hata, 3 sözleşme gereği G*Power'dan farklı)
- Tüm kontrolleri tutan vektör: **30/30**
- Karşılaştırma (§0.6): tam sayılar tam; ondalıklar |fark| ≤ 1e-6 ya da göreli fark ≤ 1e-6.
- Çağrı süresi (alt süreç, duvar saati): en yavaş **0.88 s** (G-030), ortalama 0.85 s; sınır 2 s (§0.1).

## KAPI: N tam eşleşme oranı

Payda: `n_total` beklenen a priori hesap vektörleri (post hoc'ta `n_total` artık çıktı değil; sözleşme gereği farklı vektörler hariç).

- `n_total` beklenen vektör: 14
- Tam eşleşme: 13
- Tam eşleşmesi doğrulanamayan (A-5, bilimsel gösterim): 1
- **Oran (doğrulanamayan, eşleşmemiş sayılır): 92.86%** — eşik 90% → **GEÇTİ**
- Doğrulanabilir vektörler üzerinden oran: 100.00%

## Alan bazında eşleşme

| Alan | Eşleşen | Karşılaştırılan |
|---|---|---|
| `exit_code` | 27 | 27 |
| `n_total` | 14 | 14 |
| `actual_power` | 14 | 14 |
| `critical→critical_chi2` | 20 | 20 |
| `ncp` | 20 | 20 |
| `actual_power→power` | 6 | 6 |
| `error` | 7 | 7 |
| `code` | 7 | 7 |

## Sözleşme gereği G*Power'dan farklı (§0.5)

Bu vektörlerde G*Power bir sonuç üretir; sözleşme v1.0.0 ise girdiyi reddeder. Uyuşmazlık sayılmaz; beklenen sözleşme hatası denetlenir.

| Vektör | G*Power | Sözleşme kuralı | Beklenen | Bulunan | Durum |
|---|---|---|---|---|---|
| G-019 | sonuç üretir | df tam sayı (df = 2.5) | INVALID_VALUE/df | INVALID_VALUE/df | ✔ |
| G-023 | sonuç üretir | w > 0 (w = 0) | OUT_OF_RANGE/w | OUT_OF_RANGE/w | ✔ |
| G-025 | sonuç üretir | n_total ≥ 2 (N = 1) | OUT_OF_RANGE/n_total | OUT_OF_RANGE/n_total | ✔ |

## Tutmayan vektörler

Yok.

## Açık noktalar (SPEC §5)

- **A-5** G-013: beklenen `7.8489e+12` (5 anlamlı basamak), bulunan `7848860509327`. Tam tamsayı değeri ekrandan doğrulanamaz; KAPI oranında eşleşmemiş sayıldı.
- **A-1** Parametre adları artık sözleşmede tanımlı (§0.1): `w, alpha, power, n_total, df`.
- **A-2** JSON sayıları tam double hassasiyetle yazılıyor (§0.2).
- **A-3** Post hoc'ta kesirli `n_total` sözleşme gereği `INVALID_VALUE`.
- **A-4** Kritik değer scipy `chi2.isf` ile; alan bazında `critical→critical_chi2` satırı bu kontrolün sonucudur.
