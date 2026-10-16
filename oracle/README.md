# Oracle vektörleri

Kâhin G\*Power 3.1.9.7'nin kendisidir. Beklenen değeri ajan değil G\*Power belirler.

## `vectors.csv` sütunları

| Sütun | Açıklama |
|---|---|
| `id` | `G-001` (GUI), `M-001` (kılavuz), `P-0001` (pwr/statsmodels) |
| `source` | `gui` · `manual` · `pwr` · `statsmodels` |
| `mode` | `a-priori` · `post-hoc` |
| `w`, `alpha`, `power`, `n_total_in`, `df` | Girdiler (kullanılmayan alan boş bırakılır) |
| `ncp`, `critical`, `df_out`, `n_total`, `actual_power` | G\*Power'ın ekranda gösterdiği çıktılar, **gösterildiği basamak sayısıyla** |
| `screenshot` | `screenshots/G-001.png` (GUI vektörlerinde zorunlu) |
| `notes` | Sınır değer, geçersiz girdi, hata mesajı vb. |

## Toplama kuralları

- GUI vektörü: en az 30 tane, her biri ekran görüntüsüyle.
- G\*Power yolu: Test family **χ² tests** → Statistical test **Goodness-of-fit tests: Contingency tables**.
- Sınırlar mutlaka olmalı: w çok küçük, w çok büyük, güç ≤ α, df = 1 ve büyük df, geçersiz girdiler.
- pwr/statsmodels N'yi kesirli verir, G\*Power yukarı yuvarlar. Bu satırlarda `notes` sütununa ham kesirli N yazılır.
