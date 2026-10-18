# AI ajanı değerlendirme raporu

Mimari: Sistem 1 (etiket, `claude -p --model claude-haiku-5-5`, araçsız, JSON şemalı) → MCP ajanı (`claude -p --model claude-opus-5-5`, tek araç `chi2_contingency_power`) → gpower-clone motoru. Ajan hesap yapmaz; sayılar motordan gelir.

- Değerlendirme seti: `tests/agent/eval_set.json` (10 soru)
- Kayıtlar: `tests/reports/agent/main_runs.jsonl` (20 çalıştırma), `tests/reports/agent/system1_runs.jsonl` (120 çalıştırma). Ana sonuçlar en son modelle yapılan çalıştırmalardır; öncekiler "Önceki çalıştırma" alt bölümlerinde özetlenir.
- Toplam `claude -p` çağrısı (bütün çalıştırmalar): **140**
- Ana ajan modeli (claude JSON çıktısından): claude-opus-5-5
- Sistem 1 modeli: claude-haiku-5-5

## Ana ajan (MCP yolu)

- **Doğru seçim oranı (etiket):** 10/10 (%100)
- **Doğru davranış (etiket + parametre + N/güç ya da sayısız yönlendirme):** 10/10 (%100)
- **χ² sorularında:** parametre 6/6 (%100), N 6/6 (%100), güç (7 ondalık) 6/6 (%100)
- **"Ajan sayı üretti" kontrolü:** 0 soru işaretlendi. JSON satırındaki her sayı, son başarılı araç sonucundaki değerle birebir karşılaştırılır.
- **Ek kontrol (bilgi amaçlı):** cevap metninde soruda, araç argümanında ya da araç sonucunda karşılığı olmayan sayı: Q05: 80; Q07: 1; Q08: 0,5, 0,05; Q09: 0,80, 3; Q10: 1, 2, 3, 4, 0,05, 0,01, 5, 80, 90. (Tablo boyutu ve madde numaraları gibi zararsız sayılar da burada görünebilir.)

| Soru | Beklenen | Ajan etiketi | Araç argümanları | n_total | actual_power | Beklenen N / güç | Davranış | Sayı üretti |
|---|---|---|---|---|---|---|---|---|
| Q01 | chi2-contingency | chi2-contingency | mode=a-priori, w=0.3, alpha=0.05, power=0.95, rows=2, cols=2 | 145 | 0.9507851454132252 | 145 / 0.9507851 | ✔ | hayır |
| Q02 | chi2-contingency | chi2-contingency | mode=a-priori, w=0.3, alpha=0.05, power=0.8, rows=3, cols=3 | 133 | 0.8013043469103786 | 133 / 0.8013043 | ✔ | hayır |
| Q03 | chi2-contingency | chi2-contingency | mode=a-priori, w=0.1, alpha=0.05, power=0.8, rows=2, cols=3 | 964 | 0.8002316357919949 | 964 / 0.8002316 | ✔ | hayır |
| Q04 | chi2-contingency | chi2-contingency | mode=a-priori, w=0.5, alpha=0.01, power=0.9, rows=4, cols=3 | 93 | 0.9011611358314287 | 93 / 0.9011611 | ✔ | hayır |
| Q05 | chi2-contingency | chi2-contingency | mode=post-hoc, w=0.3, alpha=0.05, n=100, rows=2, cols=2 | 100 | 0.850838768327056 | 100 / 0.8508388 | ✔ | hayır |
| Q06 | chi2-contingency | chi2-contingency | mode=post-hoc, w=0.25, alpha=0.05, n=200, rows=4, cols=3 | 200 | 0.7584629788448121 | 200 / 0.7584630 | ✔ | hayır |
| Q07 | t2-indep | t2-indep | — | None | None | yönlendir / sor | ✔ | hayır |
| Q08 | t-paired | t-paired | — | None | None | yönlendir / sor | ✔ | hayır |
| Q09 | anova-oneway | anova-oneway | — | None | None | yönlendir / sor | ✔ | hayır |
| Q10 | ambiguous | ambiguous | — | None | None | yönlendir / sor | ✔ | hayır |

### MCP yolu: token ve süre

| Soru | Girdi | Önbellek yazma | Önbellek okuma | Çıktı | Toplam | Araç çağrısı | Tur | Süre (s, duvar) | Süre (s, API) |
|---|---|---|---|---|---|---|---|---|---|
| Q01 | 4 | 3065 | 2799 | 464 | 6332 | 1 | 2 | 10.3 | 6.6 |
| Q02 | 4 | 1081 | 4722 | 562 | 6369 | 1 | 2 | 10.7 | 7.7 |
| Q03 | 4 | 1093 | 4734 | 481 | 6312 | 1 | 2 | 12.9 | 9.9 |
| Q04 | 4 | 1100 | 4745 | 455 | 6304 | 1 | 2 | 9.3 | 6.4 |
| Q05 | 4 | 1066 | 4714 | 601 | 6385 | 1 | 2 | 10.7 | 7.8 |
| Q06 | 4 | 1079 | 4725 | 413 | 6221 | 1 | 2 | 31.5 | 28.7 |
| Q07 | 2 | 818 | 1953 | 517 | 3290 | 0 | 1 | 9.3 | 6.3 |
| Q08 | 2 | 786 | 1953 | 456 | 3197 | 0 | 1 | 9.0 | 6.0 |
| Q09 | 2 | 794 | 1953 | 376 | 3125 | 0 | 1 | 7.2 | 4.0 |
| Q10 | 2 | 758 | 1953 | 563 | 3276 | 0 | 1 | 13.1 | 9.9 |
| **Toplam** | 32 | 11640 | 34251 | 4888 | **50811** | | | **124.0** | 93.2 |

Ajanın erişebildiği araçlar (claude `init` olayından): mcp__gpower-clone__chi2_contingency_power

### Önceki çalıştırma (claude-opus-4-8)

`--model opus` ile yapıldı; ana sonuç değildir, karşılaştırma için korunur.

- Etiket: 10/10 (%100)
- Davranış: 9/10 (%90) (✘: Q03)
- χ² N: 6/6 (%100), güç: 5/6 (%83); "ajan sayı üretti": 0
- Toplam token: 47126; toplam süre: 88.6 s

## Sistem 1 (etiket sınıflandırıcı)

Her soru Türkçe ve İngilizce olarak 3 kez çalıştırıldı (60 çağrı). Kural: confidence < 0.75 ya da etiket ambiguous/unsupported → araştırmacıya sor; chi2-contingency → ana ajan; diğer bilinen aileler → desteklenmiyor, yönlendir.

| Dil | Etiket doğruluğu | Yönlendirme doğruluğu | Geçersiz çıktı | Ort. güven |
|---|---|---|---|---|
| TR | 30/30 (%100) | 30/30 (%100) | 0 | 0.93 |
| EN | 30/30 (%100) | 30/30 (%100) | 0 | 0.94 |

### Soru bazında (tüm tekrarlar)

| Soru | Beklenen | TR tahminleri | EN tahminleri | TR yönlendirme | EN yönlendirme |
|---|---|---|---|---|---|
| Q01 | chi2-contingency | chi2-contingency (0.95), chi2-contingency (0.97), chi2-contingency (0.93) | chi2-contingency (0.95), chi2-contingency (0.93), chi2-contingency (0.93) | agent, agent, agent | agent, agent, agent |
| Q02 | chi2-contingency | chi2-contingency (0.95), chi2-contingency (0.93), chi2-contingency (0.95) | chi2-contingency (0.95), chi2-contingency (0.95), chi2-contingency (0.93) | agent, agent, agent | agent, agent, agent |
| Q03 | chi2-contingency | chi2-contingency (0.92), chi2-contingency (0.95), chi2-contingency (0.90) | chi2-contingency (0.93), chi2-contingency (0.85), chi2-contingency (0.95) | agent, agent, agent | agent, agent, agent |
| Q04 | chi2-contingency | chi2-contingency (0.90), chi2-contingency (0.95), chi2-contingency (0.93) | chi2-contingency (0.95), chi2-contingency (0.95), chi2-contingency (0.95) | agent, agent, agent | agent, agent, agent |
| Q05 | chi2-contingency | chi2-contingency (0.95), chi2-contingency (0.95), chi2-contingency (0.93) | chi2-contingency (0.90), chi2-contingency (0.93), chi2-contingency (0.93) | agent, agent, agent | agent, agent, agent |
| Q06 | chi2-contingency | chi2-contingency (0.95), chi2-contingency (0.97), chi2-contingency (0.95) | chi2-contingency (0.97), chi2-contingency (0.95), chi2-contingency (0.93) | agent, agent, agent | agent, agent, agent |
| Q07 | t2-indep | t2-indep (0.97), t2-indep (0.95), t2-indep (0.97) | t2-indep (0.97), t2-indep (0.97), t2-indep (0.95) | refer, refer, refer | refer, refer, refer |
| Q08 | t-paired | t-paired (0.95), t-paired (0.95), t-paired (0.90) | t-paired (0.97), t-paired (0.97), t-paired (0.95) | refer, refer, refer | refer, refer, refer |
| Q09 | anova-oneway | anova-oneway (0.95), anova-oneway (0.95), anova-oneway (0.95) | anova-oneway (0.95), anova-oneway (0.95), anova-oneway (0.95) | refer, refer, refer | refer, refer, refer |
| Q10 | ambiguous | ambiguous (0.85), ambiguous (0.85), ambiguous (0.85) | ambiguous (0.90), ambiguous (0.90), ambiguous (0.90) | ask, ask, ask | ask, ask, ask |

### Kalibrasyon

Güven aralığına düşen tahminlerin gerçek doğruluğu ("%90 güven" dediklerinin kaçı doğru).

| Aralık | TR n | TR ort. güven | TR doğruluk | EN n | EN ort. güven | EN doğruluk | Tümü n | Tümü doğruluk |
|---|---|---|---|---|---|---|---|---|
| 0.9–1.0 | 27 | 0.94 | %100 | 29 | 0.94 | %100 | 56 | %100 |
| 0.75–0.9 | 3 | 0.85 | %100 | 1 | 0.85 | %100 | 4 | %100 |
| <0.75 | 0 | — | — | 0 | — | — | 0 | — |

### Önceki çalıştırma (claude-haiku-4-5-20251001)

`--model haiku`, 60 çağrı; ana sonuç değildir.

- TR: etiket 29/30 (%97), yönlendirme 30/30 (%100)
- EN: etiket 28/30 (%93), yönlendirme 30/30 (%100)
- Toplam token: 175959; toplam süre: 673.5 s

Sistem 1 toplam token: girdi 120, önbellek yazma 15238, önbellek okuma 80921, çıktı 13203; toplam süre 202.1 s.

## MCP ↔ GUI karşılaştırması

Token sütunları: girdi / önbellek yazma / önbellek okuma / çıktı.

| Soru | MCP token | MCP toplam | MCP süre (s) | MCP doğru | GUI token | GUI toplam | GUI süre (s) | GUI model çağrısı | Ekran görüntüsü | GUI doğru |
|---|---|---|---|---|---|---|---|---|---|---|
| Q01 | 4 / 3065 / 2799 / 464 | 6332 | 10.3 | ✔ | 20 / 12040 / 1153983 / 4224 | 1170267 | 56.5 | 10 | 7 | ✔ |
| Q02 | 4 / 1081 / 4722 / 562 | 6369 | 10.7 | ✔ | 4 / 2173 / 245213 / 1080 | 248470 | 11.7 | 2 | 1 | ✔ |
| Q03 | 4 / 1093 / 4734 / 481 | 6312 | 12.9 | ✔ | 4 / 1467 / 249016 / 901 | 251388 | 9.8 | 2 | 1 | ✔ |
| Q04 | 4 / 1100 / 4745 / 455 | 6304 | 9.3 | ✔ | 4 / 1945 / 251962 / 1205 | 255116 | 12.0 | 2 | 1 | ✔ |
| Q05 | 4 / 1066 / 4714 / 601 | 6385 | 10.7 | ✔ | 8 / 3556 / 515113 / 1505 | 520182 | 19.6 | 4 | 3 | ✔ |
| Q06 | 4 / 1079 / 4725 / 413 | 6221 | 31.5 | ✔ | 8 / 2220 / 529100 / 1870 | 533198 | 20.0 | 4 | 3 | ✔ |
| Q07 | 2 / 818 / 1953 / 517 | 3290 | 9.3 | ✔ | 0 / 0 / 0 / 0 | 0 | 0.0 | 0 | 0 | ✔ |
| Q08 | 2 / 786 / 1953 / 456 | 3197 | 9.0 | ✔ | 0 / 0 / 0 / 0 | 0 | 0.0 | 0 | 0 | ✔ |
| Q09 | 2 / 794 / 1953 / 376 | 3125 | 7.2 | ✔ | 0 / 0 / 0 / 0 | 0 | 0.0 | 0 | 0 | ✔ |
| Q10 | 2 / 758 / 1953 / 563 | 3276 | 13.1 | ✔ | 0 / 0 / 0 / 0 | 0 | 0.0 | 0 | 0 | ✔ |
| **Toplam (sorular)** | | **50811** | **124.0** | **10/10** | | **2978621** | **129.8** | **24** | **16** | **10/10** |
| GUI hazırlık | | | | | 10 / 86161 / 406983 / 1451 | 494605 | | 5 | | |
| GUI kapanış | | | | | 4 / 2274 / 268886 / 1982 | 273146 | | 2 | | |
| **Hazırlık dahil toplam** | | **50811** | | | | **3746372** | | **31** | | |

- Yalnızca soru pencereleri: GUI yolu MCP yolunun **58.6×** token'ını ve **1.0×** süresini harcadı.
- Hazırlık ve kapanış dahil: GUI **3746372**, MCP **50811** token (**73.7×**).
- Doğruluk: MCP 10/10, GUI 10/10.

**Adalet notu.** MCP yolu her soruyu ayrı bir `claude -p` çağrısında çözer; her soru kendi başlangıç maliyetini (sistem prompt'u, araç şeması, Claude Code'un arka plan çağrıları) taşır ve ayrı bir hazırlık maliyeti yoktur. GUI yolu tek uzun bir konuşmadır; her çağrı birikmiş geçmişi ve ekran görüntülerini yeniden okur (önbellek okuma sütunu), G\*Power'ı açma ve kapanış özeti gibi pencere dışı çağrılar `gui_overhead.json` içinde ayrıca sayılır. Q07–Q10'da GUI kullanılmadı ve o pencerelerde model çağrısı yok; bu sorularda GUI satırının sıfır olması, kararın daha önceki bir çağrıda verildiği anlamına gelir.

**Model notu.** MCP yolu `--model claude-opus-5-5` ile çalıştı; claude çıktısındaki ana model: claude-opus-5-5 (modelUsage: claude-opus-5-5; varsa küçük model Claude Code'un arka plan çağrısıdır). GUI yolu, ölçümü yapan oturumun bildirdiğine göre Opus 5.5 ile koştu. İki yol aynı ana modeli kullanıyor. MCP süresi `claude -p` sürecinin duvar saatidir: süreç başlatma ve MCP sunucusunun açılışı dahildir.
