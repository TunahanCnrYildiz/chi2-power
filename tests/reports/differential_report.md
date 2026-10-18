# Diferansiyel test raporu (G*Power kâhini ↔ gpower-clone)

- Kaynak: `oracle\vectors.csv`
- Toplam vektör: **30** (23 hesap, 7 hata)
- Tüm alanları tutan vektör: **30/30**

## KAPI: N tam eşleşme oranı

- `n_total` beklenen vektör: 15
- Tam eşleşme: 14
- Tam eşleşmesi doğrulanamayan (A-5, bilimsel gösterim): 1
- **Oran (doğrulanamayan, eşleşmemiş sayılır): 93.33%** — eşik 90% → **GEÇTİ**
- Doğrulanabilir vektörler üzerinden oran: 100.00%

## Alan bazında eşleşme

| Alan | Eşleşen | Karşılaştırılan |
|---|---|---|
| `exit_code` | 30 | 30 |
| `n_total` | 15 | 15 |
| `actual_power` | 23 | 23 |
| `critical` | 23 | 23 |
| `ncp` | 23 | 23 |
| `error` | 7 | 7 |

## Tutmayan vektörler

Yok.

## Açık noktalar (SPEC §5)

- **A-5** G-013: beklenen `7.8489e+12` (5 anlamlı basamak), bulunan `7848860509327`. Tam tamsayı değeri ekrandan doğrulanamaz; KAPI oranında eşleşmemiş sayıldı.
- **A-1** Parametre adları (`--w`, `--df`, `--n`) CONTRACT.md ile doğrulanmadı; eş adlar `--n-total`, `--n_total`, `--mode posthoc` kabul ediliyor.
- **A-2** JSON sayıları tam hassasiyetle (yuvarlamasız double) yazılıyor.
- **A-3** Post hoc'ta kesirli N hata veriyor (tasarım kararı); G*Power davranışı gözlenmedi.
- **A-4** Kritik değer scipy `chi2.isf` ile; G*Power'ın iç quantile yöntemi bilinmiyor. Alan bazında `critical` satırı bu kontrolün sonucudur.
