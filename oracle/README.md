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

## Kılavuz örnekleri

G\*Power 3.1 kılavuzunda (1 Haziran 2023) "Goodness-of-fit tests: Contingency tables" için çalışılmış örnek **yoktur**; kılavuzda bu teste ayrılmış bir bölüm bulunmaz (LEDGER L-032). Bu nedenle bu aile için "kılavuz örneği" türünde vektör eklenemedi; davranış GUI vektörleri (G-001 – G-030) ve binary kanıtlarıyla belirlendi.

## Ekrandaki basamak sayısı

G\*Power değerleri çoğunlukla 7 ondalıkla gösterir, ancak tamsayı değerli λ ondalıksız (`0`, `1000`), büyük kritik değer 4 ondalıkla (`149.4493`), çok büyük N bilimsel gösterimle (`7.8489e+12`) görünür. CSV değerleri ekrandaki metin olarak saklar; karşılaştırma bu basamak sayısıyla yapılır.
