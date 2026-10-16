# Kanıt Defteri (LEDGER)

Kapsam: G\*Power 3.1.9.7 · `GPowerNT.exe` (SHA-256 `C63E6A13…EFC812`) · χ² olumsallık tablosu.

## Etiketler

| Etiket | Anlamı | Puan |
|---|---|---|
| `[DOK]` | Kılavuzda ya da makalede yazıyor (sayfa/bölüm belirtilir). | — |
| `[REA]` | Binary'den kanıtlandı: fonksiyon adresi ve/veya dize referansı. | ✔ |
| `[AJAN]` | Ajanın çıkarımı, kanıtı yok. Diferansiyel testle sınanmalı. | — |

Kurallar:
- Her satır **tek bir iddia** içerir ve bir kimliği vardır (`L-001`, `L-002`, …).
- `[REA]` satırı: adres (`0x…`), araç (REA aracı ya da Ghidra), kısa alıntı (en fazla birkaç satır, decompile dökümü değil).
- `[AJAN]` satırı sonradan kanıtlanırsa silinmez; durumu güncellenir ve yeni bir `[REA]` satırına bağlanır.
- `Test` sütunu, iddiayı sınayan oracle vektörünü ya da testi gösterir.
- Yanlış çıkan iddialar `HALLUCINATIONS.md`'ye taşınır.

## Kılavuzda olmayan davranışlar (öncelikli av listesi)

- [ ] A priori N araması: başlangıç değeri, adım stratejisi, durma koşulu
- [ ] Yuvarlama: N tamsayıya nasıl getiriliyor (tavan mı, arama mı?)
- [ ] "Actual power" hangi N ile hesaplanıyor
- [ ] Merkezi olmayan χ² dağılımının hesap yöntemi ve hassasiyeti
- [ ] Kritik χ² değerinin hesabı (ters CDF yöntemi)
- [ ] Sınırlar: df = 0, w = 0, w çok büyük, güç ≤ α, α ≥ 1
- [ ] Geçersiz girdiye tepki (hata mesajı dizeleri)

## Defter

| ID | Etiket | İddia | Kanıt (adres / dize / kaynak) | Test | Durum |
|---|---|---|---|---|---|
| L-001 | `[AJAN]` | Merkezi olmama parametresi λ = w² · N. | İlk ilkelerden; binary'de doğrulanmadı. | — | açık |
