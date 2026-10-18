# AI ajanı değerlendirme raporu

Mimari: Sistem 1 (etiket, `claude -p --model haiku`, araçsız, JSON şemalı) → MCP ajanı (`claude -p --model opus`, tek araç `chi2_contingency_power`) → gpower-clone motoru. Ajan hesap yapmaz; sayılar motordan gelir.

- Değerlendirme seti: `tests/agent/eval_set.json` (10 soru)
- Kayıtlar: `tests/reports/agent/main_runs.jsonl` (10 çalıştırma), `tests/reports/agent/system1_runs.jsonl` (60 çalıştırma)
- Toplam `claude -p` çağrısı: **70**
- Ana ajan modeli (claude JSON çıktısından): claude-haiku-4-5-20251001, claude-opus-4-8
- Sistem 1 modeli: claude-haiku-4-5-20251001

## Ana ajan (MCP yolu)

- **Doğru seçim oranı (etiket):** 10/10 (%100)
- **Doğru davranış (etiket + parametre + N/güç ya da sayısız yönlendirme):** 9/10 (%90)
- **χ² sorularında:** parametre 6/6 (%100), N 6/6 (%100), güç (7 ondalık) 5/6 (%83)
- **"Ajan sayı üretti" kontrolü:** 0 soru işaretlendi. JSON satırındaki her sayı, son başarılı araç sonucundaki değerle birebir karşılaştırılır.
- **Ek kontrol (bilgi amaçlı):** cevap metninde soruda, araç argümanında ya da araç sonucunda karşılığı olmayan sayı: Q10: 1, 2, 3, 4, 0,05, 0,80. (Tablo boyutu ve madde numaraları gibi zararsız sayılar da burada görünebilir.)

| Soru | Beklenen | Ajan etiketi | Araç argümanları | n_total | actual_power | Beklenen N / güç | Davranış | Sayı üretti |
|---|---|---|---|---|---|---|---|---|
| Q01 | chi2-contingency | chi2-contingency | mode=a-priori, w=0.3, alpha=0.05, power=0.95, rows=2, cols=2 | 145 | 0.9507851454132252 | 145 / 0.9507851 | ✔ | hayır |
| Q02 | chi2-contingency | chi2-contingency | mode=a-priori, w=0.3, alpha=0.05, power=0.8, rows=3, cols=3 | 133 | 0.8013043469103786 | 133 / 0.8013043 | ✔ | hayır |
| Q03 | chi2-contingency | chi2-contingency | mode=a-priori, w=0.1, alpha=0.05, power=0.8, rows=2, cols=3 | 964 | None | 964 / 0.8002316 | ✘ | hayır |
| Q04 | chi2-contingency | chi2-contingency | mode=a-priori, w=0.5, alpha=0.01, power=0.9, rows=4, cols=3 | 93 | 0.9011611358314287 | 93 / 0.9011611 | ✔ | hayır |
| Q05 | chi2-contingency | chi2-contingency | mode=post-hoc, w=0.3, alpha=0.05, n=100, rows=2, cols=2 | 100 | 0.850838768327056 | 100 / 0.8508388 | ✔ | hayır |
| Q06 | chi2-contingency | chi2-contingency | mode=post-hoc, w=0.25, alpha=0.05, rows=4, cols=3, n=200 | 200 | 0.7584629788448121 | 200 / 0.7584630 | ✔ | hayır |
| Q07 | t2-indep | t2-indep | — | None | None | yönlendir / sor | ✔ | hayır |
| Q08 | t-paired | t-paired | — | None | None | yönlendir / sor | ✔ | hayır |
| Q09 | anova-oneway | anova-oneway | — | None | None | yönlendir / sor | ✔ | hayır |
| Q10 | ambiguous | ambiguous | — | None | None | yönlendir / sor | ✔ | hayır |

### MCP yolu: token ve süre

| Soru | Girdi | Önbellek yazma | Önbellek okuma | Çıktı | Toplam | Araç çağrısı | Tur | Süre (s, duvar) | Süre (s, API) |
|---|---|---|---|---|---|---|---|---|---|
| Q01 | 636 | 2558 | 2282 | 351 | 5827 | 1 | 2 | 8.6 | 5.4 |
| Q02 | 609 | 667 | 4116 | 356 | 5748 | 1 | 2 | 8.2 | 5.1 |
| Q03 | 629 | 675 | 4128 | 357 | 5789 | 1 | 2 | 8.4 | 5.3 |
| Q04 | 627 | 685 | 4139 | 353 | 5804 | 1 | 2 | 8.4 | 5.2 |
| Q05 | 608 | 647 | 4108 | 335 | 5698 | 1 | 2 | 7.8 | 4.7 |
| Q06 | 619 | 662 | 4119 | 371 | 5771 | 1 | 2 | 8.6 | 5.6 |
| Q07 | 612 | 390 | 1864 | 209 | 3075 | 0 | 1 | 6.7 | 3.6 |
| Q08 | 583 | 358 | 1864 | 249 | 3054 | 0 | 1 | 7.8 | 4.8 |
| Q09 | 594 | 366 | 1864 | 270 | 3094 | 0 | 1 | 7.7 | 4.6 |
| Q10 | 558 | 330 | 1864 | 514 | 3266 | 0 | 1 | 16.4 | 13.3 |
| **Toplam** | 6075 | 7338 | 30348 | 3365 | **47126** | | | **88.6** | 57.6 |

Ajanın erişebildiği araçlar (claude `init` olayından): mcp__gpower-clone__chi2_contingency_power

## Sistem 1 (etiket sınıflandırıcı)

Her soru Türkçe ve İngilizce olarak 3 kez çalıştırıldı (60 çağrı). Kural: confidence < 0.75 ya da etiket ambiguous/unsupported → araştırmacıya sor; chi2-contingency → ana ajan; diğer bilinen aileler → desteklenmiyor, yönlendir.

| Dil | Etiket doğruluğu | Yönlendirme doğruluğu | Geçersiz çıktı | Ort. güven |
|---|---|---|---|---|
| TR | 29/30 (%97) | 30/30 (%100) | 0 | 0.96 |
| EN | 28/30 (%93) | 30/30 (%100) | 0 | 0.97 |

### Soru bazında (tüm tekrarlar)

| Soru | Beklenen | TR tahminleri | EN tahminleri | TR yönlendirme | EN yönlendirme |
|---|---|---|---|---|---|
| Q01 | chi2-contingency | chi2-contingency (0.99), chi2-contingency (0.98), chi2-contingency (0.95) | chi2-contingency (0.98), chi2-contingency (0.98), chi2-contingency (0.96) | agent, agent, agent | agent, agent, agent |
| Q02 | chi2-contingency | chi2-contingency (0.95), chi2-contingency (0.98), chi2-contingency (0.98) | chi2-contingency (0.98), chi2-contingency (0.98), chi2-contingency (0.98) | agent, agent, agent | agent, agent, agent |
| Q03 | chi2-contingency | chi2-contingency (0.98), chi2-contingency (0.95), chi2-contingency (0.95) | chi2-contingency (0.98), chi2-contingency (0.98), chi2-contingency (0.98) | agent, agent, agent | agent, agent, agent |
| Q04 | chi2-contingency | chi2-contingency (0.98), chi2-contingency (0.98), chi2-contingency (0.95) | chi2-contingency (0.96), chi2-contingency (0.95), chi2-contingency (0.95) | agent, agent, agent | agent, agent, agent |
| Q05 | chi2-contingency | chi2-contingency (0.98), chi2-contingency (0.98), chi2-contingency (0.95) | chi2-contingency (0.95), chi2-contingency (0.98), chi2-contingency (0.97) | agent, agent, agent | agent, agent, agent |
| Q06 | chi2-contingency | chi2-contingency (0.98), chi2-contingency (0.98), chi2-contingency (0.95) | chi2-contingency (0.98), chi2-contingency (0.98), chi2-contingency (0.98) | agent, agent, agent | agent, agent, agent |
| Q07 | t2-indep | t2-indep (0.98), t2-indep (0.98), t2-indep (0.98) | t2-indep (0.96), t2-indep (0.99), t2-indep (0.95) | refer, refer, refer | refer, refer, refer |
| Q08 | t-paired | t-paired (0.98), t-paired (0.95), t-paired (0.95) | t-paired (0.98), t-paired (0.92), t-paired (0.92) | refer, refer, refer | refer, refer, refer |
| Q09 | anova-oneway | anova-oneway (0.98), anova-oneway (0.95), anova-oneway (0.98) | anova-oneway (0.98), anova-oneway (0.98), anova-oneway (0.95) | refer, refer, refer | refer, refer, refer |
| Q10 | ambiguous | unsupported (0.75), ambiguous (0.92), ambiguous (0.95) | unsupported (0.95), ambiguous (0.95), unsupported (0.95) | ask, ask, ask | ask, ask, ask |

### Kalibrasyon

Güven aralığına düşen tahminlerin gerçek doğruluğu ("%90 güven" dediklerinin kaçı doğru).

| Aralık | TR n | TR ort. güven | TR doğruluk | EN n | EN ort. güven | EN doğruluk | Tümü n | Tümü doğruluk |
|---|---|---|---|---|---|---|---|---|
| 0.9–1.0 | 29 | 0.97 | %100 | 30 | 0.97 | %93 | 59 | %97 |
| 0.75–0.9 | 1 | 0.75 | %0 | 0 | — | — | 1 | %0 |
| <0.75 | 0 | — | — | 0 | — | — | 0 | — |

Sistem 1 toplam token: girdi 112887, önbellek yazma 0, önbellek okuma 0, çıktı 63072; toplam süre 673.5 s.

## MCP ↔ GUI karşılaştırması

Token sütunları: girdi / önbellek yazma / önbellek okuma / çıktı.

| Soru | MCP token | MCP toplam | MCP süre (s) | MCP doğru | GUI token | GUI toplam | GUI süre (s) | GUI model çağrısı | Ekran görüntüsü | GUI doğru |
|---|---|---|---|---|---|---|---|---|---|---|
| Q01 | 636 / 2558 / 2282 / 351 | 5827 | 8.6 | ✔ | 20 / 12040 / 1153983 / 4224 | 1170267 | 56.5 | 10 | 7 | ✔ |
| Q02 | 609 / 667 / 4116 / 356 | 5748 | 8.2 | ✔ | 4 / 2173 / 245213 / 1080 | 248470 | 11.7 | 2 | 1 | ✔ |
| Q03 | 629 / 675 / 4128 / 357 | 5789 | 8.4 | ✘ | 4 / 1467 / 249016 / 901 | 251388 | 9.8 | 2 | 1 | ✔ |
| Q04 | 627 / 685 / 4139 / 353 | 5804 | 8.4 | ✔ | 4 / 1945 / 251962 / 1205 | 255116 | 12.0 | 2 | 1 | ✔ |
| Q05 | 608 / 647 / 4108 / 335 | 5698 | 7.8 | ✔ | 8 / 3556 / 515113 / 1505 | 520182 | 19.6 | 4 | 3 | ✔ |
| Q06 | 619 / 662 / 4119 / 371 | 5771 | 8.6 | ✔ | 8 / 2220 / 529100 / 1870 | 533198 | 20.0 | 4 | 3 | ✔ |
| Q07 | 612 / 390 / 1864 / 209 | 3075 | 6.7 | ✔ | 0 / 0 / 0 / 0 | 0 | 0.0 | 0 | 0 | ✔ |
| Q08 | 583 / 358 / 1864 / 249 | 3054 | 7.8 | ✔ | 0 / 0 / 0 / 0 | 0 | 0.0 | 0 | 0 | ✔ |
| Q09 | 594 / 366 / 1864 / 270 | 3094 | 7.7 | ✔ | 0 / 0 / 0 / 0 | 0 | 0.0 | 0 | 0 | ✔ |
| Q10 | 558 / 330 / 1864 / 514 | 3266 | 16.4 | ✔ | 0 / 0 / 0 / 0 | 0 | 0.0 | 0 | 0 | ✔ |
| **Toplam (sorular)** | | **47126** | **88.6** | **9/10** | | **2978621** | **129.8** | **24** | **16** | **10/10** |
| GUI hazırlık | | | | | 10 / 86161 / 406983 / 1451 | 494605 | | 5 | | |
| GUI kapanış | | | | | 4 / 2274 / 268886 / 1982 | 273146 | | 2 | | |
| **Hazırlık dahil toplam** | | **47126** | | | | **3746372** | | **31** | | |

- Yalnızca soru pencereleri: GUI yolu MCP yolunun **63.2×** token'ını ve **1.5×** süresini harcadı.
- Hazırlık ve kapanış dahil: GUI **3746372**, MCP **47126** token (**79.5×**).
- Doğruluk: MCP 9/10, GUI 10/10.

**Adalet notu.** MCP yolu her soruyu ayrı bir `claude -p` çağrısında çözer; her soru kendi başlangıç maliyetini (sistem prompt'u, araç şeması, Claude Code'un arka plan çağrıları) taşır ve ayrı bir hazırlık maliyeti yoktur. GUI yolu tek uzun bir konuşmadır; her çağrı birikmiş geçmişi ve ekran görüntülerini yeniden okur (önbellek okuma sütunu), G\*Power'ı açma ve kapanış özeti gibi pencere dışı çağrılar `gui_overhead.json` içinde ayrıca sayılır. Q07–Q10'da GUI kullanılmadı ve o pencerelerde model çağrısı yok; bu sorularda GUI satırının sıfır olması, kararın daha önceki bir çağrıda verildiği anlamına gelir.

**Model notu.** MCP yolunda `--model opus` takma adı claude JSON çıktısına göre şu modellere çözüldü: claude-haiku-4-5-20251001, claude-opus-4-8 (küçük model, Claude Code'un arka plan çağrısıdır). GUI yolu, ölçümü yapan oturumun bildirdiğine göre Opus 5.5 ile koştu. Modeller farklı olduğu için token ve süre oranları yalnızca yaklaşık bir karşılaştırmadır. MCP süresi `claude -p` sürecinin duvar saatidir: süreç başlatma ve MCP sunucusunun açılışı dahildir.
