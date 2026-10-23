# chi2-power · χ² Olumsallık Tablosu Güç Analizi

> **Yapılan katmanlar**
> - ✅ **Temel katman (CLI):** tamamlandı; eğitmenin arayüz sözleşmesi v1.0.0 ile uyumlu. KAPI geçti: a priori N tam eşleşme %92.86; doğrulanabilir vektörlerde %100.
> - ✅ **MCP sunucusu (+15):** tamamlandı. Sözleşmedeki tek araç `power_analysis`; aynı motoru çağıran ince bir adaptör. 25 açık referans vektöründe ve 30 SPEC vektöründe CLI ile birebir aynı çıktı ([aşağıda](#mcp-sunucusu-bonus-katman)).
> - ✅ **AI ajanı (+10):** tamamlandı. Türkçe klinik soruyu MCP aracıyla yanıtlıyor. Doğru seçim 10/10. Ölçülmüş MCP ↔ GUI karşılaştırması: GUI yolu ≈ 59–74× token harcıyor. Jev yerine etiketle kısıtlı LLM kullanıldı ([aşağıda](#ai-ajanı-bonus-katman)).

G\*Power 3.1.9.7'nin **χ² testi, olumsallık tablosu** hesabının temiz oda yöntemiyle yeniden yazımıdır.
`gpower-clone` G\*Power değildir ve G\*Power ekibiyle bir bağı yoktur (bkz. [Atıf](#atıf)).

Çalışma bireyseldir.

## Hızlı başlangıç

Gereksinim: Python ≥ 3.10 (Python 3.14 ile geliştirildi ve test edildi). Kurulum tek komut:

```bash
python -m venv .venv && .venv/Scripts/python -m pip install -e ".[test,diff,mcp]"
```

Linux ve macOS'ta `.venv/Scripts/` yerine `.venv/bin/` kullanılır. Kurulumdan sonra `gpower-clone` komutu sanal ortamda hazırdır.

Arayüz, eğitmenin **arayüz sözleşmesi v1.0.0** ile uyumludur (komut, alan adları, çıktı alanları, hata biçimi). Sözleşme gereği kararlar SPEC §0'da.

**A priori: gereken toplam N**

```bash
gpower-clone --test chi2-contingency --mode a-priori --w 0.3 --alpha 0.05 --power 0.95 --df 5
```

```json
{"ncp":19.8,"critical_chi2":11.070497693516355,"n_total":220,"actual_power":0.9502155018970163}
```

**Post hoc: ulaşılan güç**

```bash
gpower-clone --test chi2-contingency --mode post-hoc --w 0.3 --alpha 0.05 --n_total 100 --df 5
```

```json
{"ncp":9.0,"critical_chi2":11.070497693516355,"power":0.6235846116825698}
```

**Geçersiz girdi.** Tek satır JSON hata verir; çıkış kodu `2`:

```bash
gpower-clone --test chi2-contingency --mode a-priori --w 0.3 --alpha 0.05 --power 0.04 --df 1
```

```json
{"error":"Power must be greater than or equal to alpha.","code":"INCONSISTENT","field":"power"}
```

**Sürüm sorgusu**

```bash
gpower-clone --version
```

```json
{"contract_version":"1.0.0","name":"chi2-power","engine":"Python 3.14.6, scipy 1.18.1"}
```

`python -m gpower_clone …` de aynı şekilde çalışır.

### CLI sözleşmesi (χ² olumsallık tablosu)

| Mod | Girdi alanları | Çıktı alanları |
|---|---|---|
| `a-priori` | `w`, `alpha`, `power`, `df` | `ncp`, `critical_chi2`, `n_total`, `actual_power` |
| `post-hoc` | `w`, `alpha`, `n_total`, `df` | `ncp`, `critical_chi2`, `power` |

| Alan | Tür | Geçerli aralık |
|---|---|---|
| `w` | ondalık | > 0 (sözleşme); a priori'de G\*Power gibi ≥ 1e-6 |
| `alpha` | ondalık | 0 < α < 1 (sözleşme); G\*Power'ın aralığı [1e-7, 0.9999999] |
| `power` | ondalık | 0 < güç < 1; G\*Power'ın aralığı [1e-7, 0.9999999] ve güç ≥ α |
| `n_total` | tam sayı | ≥ 2 (sözleşme); G\*Power'ın üst sınırı 2147483646 |
| `df` | tam sayı | ≥ 1 |

- **Kurallar:** Varsayılan değer yoktur. Eksik alan `MISSING_PARAM`, tanınmayan ya da modla ilgisiz alan `UNKNOWN_PARAM` hatasıdır (ör. post hoc'ta `--power`, χ²'de `--tails`).
- **Sayılar:** Tam double hassasiyetle yazılır; `n_total` JSON tam sayısıdır. Yalnızca tabloda listelenen alanlar yazılır.
- **Hatalar:** Biçim `{"error", "code", "field"}`. Kodlar `MISSING_PARAM`, `UNKNOWN_PARAM`, `INVALID_VALUE`, `OUT_OF_RANGE`, `INCONSISTENT`, `UNSUPPORTED`, `NO_SOLUTION`. Çıkış kodu girdi hatasında `2`, iç hatada `1`. `error` metni mümkün olan her yerde G\*Power'ın kendi mesajıdır.
- **Sözleşme ile G\*Power'ın farklı olduğu üç nokta:** Sözleşme aralıkları G\*Power'dan sıkı. G\*Power'ın kabul ettiği kesirli df (G-019), post hoc'ta w = 0 (G-023) ve N = 1 (G-025) burada **reddedilir**. Raporlarda bunlar ayrıca "sözleşme gereği farklı" diye gösterilir.
- **Uzantı:** Ajan katmanı için `df` yerine `rows` + `cols` verilebilir; df'yi motor hesaplar. Sözleşmede yoktur ve test düzeneği bunu kullanmaz.
- **Kapsam:** Diğer test aileleri (`t2-indep`, `t-paired`, `anova-oneway`, `multireg-r2`) `UNSUPPORTED` döndürür.

### Testler ve raporlar

```bash
.venv/Scripts/python -m pytest -q
.venv/Scripts/python tests/differential.py --csv oracle/vectors.csv --report tests/reports/differential_report.md
.venv/Scripts/python tests/statsmodels_vectors.py
```

- `pytest` şunları kapsar:
  - SPEC §6'nın her vektörü ayrı bir kabul testi,
  - sözleşme testleri (25 açık referans vektörü dahil),
  - motor ve CLI birim testleri,
  - G\*Power kâhinine karşı KAPI testi,
  - 894 vektörlük statsmodels regresyonu,
  - MCP ve ajan testleri (ajan testleri sahte bir `claude` çalıştırıcısıyla; gerçek ölçümler `python -m gpower_clone.agent.evaluate` ile).
- `differential.py` CLI'yi gerçek bir alt süreç olarak çalıştırır ve sonucu sözleşmenin toleransıyla karşılaştırır: tam sayılar tam eşleşmeli, ondalıklarda mutlak ya da göreli fark ≤ 1e-6.
- `statsmodels_vectors.py` statsmodels `GofChisquarePower` ile 894 vektör üretir ve karşılaştırır.

## Sonuçlar

| Ölçüm | Sonuç | Kaynak |
|---|---|---|
| pytest | **267 geçti, 0 atlandı** | `tests/` |
| Sözleşmenin açık referans vektörleri (χ²) | a priori N = 220, güç 0.9502155; post hoc güç 0.6235846, **1e-6 toleransla tutuyor** | [`tests/fixtures/public_vectors.jsonl`](tests/fixtures/public_vectors.jsonl) |
| G\*Power arayüz vektörleri (kâhin) | **30/30** vektör beklenen sonucu veriyor: 20 hesap, 7 G\*Power hata mesajı, 3 sözleşme farkı | [`tests/reports/differential_report.md`](tests/reports/differential_report.md) |
| **KAPI** (a priori N tam eşleşme, eşik %90) | **%92.86 → GEÇTİ.** Doğrulanabilir vektörlerde %100. | aynı rapor |
| statsmodels ölçek testi | 894 vektör (594 a priori, 300 post hoc), **uyuşmazlık yok** | [`tests/reports/statsmodels_report.md`](tests/reports/statsmodels_report.md) |
| MCP ↔ CLI eşdeğerliği | 25 açık referans vektörü ve 30 SPEC vektöründe **birebir aynı JSON**; stdio üzerinden uçtan uca test geçti | `tests/test_mcp.py`, `tests/test_contract.py` |

KAPI oranı temkinli hesaplandı:
- Payda yalnızca a priori `n_total` vektörlerinden oluşuyor (14 vektör).
- G-013'te (w = 1e-6) G\*Power N'yi ekranda yalnızca `7.8489e+12` olarak gösteriyor. Bizim değerimiz 7 848 860 509 327 ve bu gösterimle uyumlu, ama tam tamsayı ekrandan doğrulanamadığı için bu vektörü "eşleşmedi" saydık (SPEC §5, A-5).
- Eşleşmeyen tek vektör bu; geri kalan 13 vektörün hepsi tam eşleşiyor.

### Bulgu: kesirli N → tamsayı N

pwr ve statsmodels N'yi kesirli verir, G\*Power ise tamsayıya çevirir. Kılavuz bunu "kesirli N her zaman yukarı yuvarlanır" diye anlatıyor (LEDGER L-030 `[DOK]`). Binary ise **kılavuzda olmayan** bir ara adım içeriyor (L-021 `[REA]`): N önce 10 ondalık basamağa yuvarlanıyor, sonra yukarı yuvarlanıyor. Bu yüzden kesirli kısmı 5·10⁻¹¹'den küçük bir N aşağı iner; örneğin 104.00000000003 → 104. 594 a priori statsmodels vektörünün hepsinde `n_total = ⌈N_statsmodels⌉`. Hiçbir kök bir tamsayıya bu kadar yakın olmadığından bu ızgarada iki kural ayrışmadı.

## MCP sunucusu (bonus katman)

**Mimari.** MCP sunucusu, CLI ile **aynı motoru** çağıran ince bir adaptördür. Akış:

```
CLI (cli.py)       ─┐
                    ├─► service.compute ─► engine (hesap ve doğrulamanın tek yeri)
MCP (mcp_server.py) ─┘
```

- `mcp_server.py` yalnızca argümanları alır ve `service.compute` fonksiyonunu çağırır; içinde hesap kodu yoktur.
- Testler bunu kaynak kodu düzeyinde denetler: MCP modülünde scipy, `math`, sayı dönüştürme ya da motor fonksiyonu geçmez.
- Teknik ayrıntılar: resmi Python MCP SDK'sı (`mcp` 2.3) ve stdio taşıma.

**Çalıştırma**

```bash
.venv/Scripts/python -m pip install -e ".[mcp]"
gpower-clone-mcp
```

Sunucu `python -m gpower_clone.mcp_server` ile de başlatılabilir.

**Kayıt.** Claude Code'a eklemek için:

```bash
claude mcp add gpower-clone -- "<repo>/.venv/Scripts/gpower-clone-mcp.exe"
```

Claude Desktop'a eklemek için `claude_desktop_config.json` dosyasına:

```json
{ "mcpServers": { "gpower-clone": { "command": "<repo>/.venv/Scripts/gpower-clone-mcp.exe", "args": [] } } }
```

### Araç şeması: `power_analysis`

Arayüz sözleşmesine göre tek araç vardır. Alan adları CLI ile aynıdır; `test` ve `mode` zorunludur.

**Girdi** (`inputSchema`)

| Alan | Tip | Zorunlu | Açıklama |
|---|---|---|---|
| `test` | string | evet | `chi2-contingency`; diğer aileler `UNSUPPORTED` döner |
| `mode` | `"a-priori"` \| `"post-hoc"` | evet | a priori: N'yi çöz · post hoc: gücü çöz |
| `w` | number | ikisinde | Etki büyüklüğü w > 0 (a priori'de ≥ 1e-6) |
| `alpha` | number | ikisinde | α, 1e-7 … 0.9999999 |
| `power` | number | a priori'de | Hedef güç, 1e-7 … 0.9999999, ≥ α |
| `n_total` | integer | post hoc'ta | Toplam N, 2 … 2147483646 |
| `df` | integer | ikisinde | Serbestlik derecesi ≥ 1 (ya da `rows` + `cols`) |
| `rows`, `cols` | integer | — | Uzantı: tablo boyutu (≥ 2); df'yi motor hesaplar |

**Çıktı.**
- Başarıda metin içeriği, CLI'nin stdout JSON satırıyla **birebir aynıdır**: a priori'de `ncp`, `critical_chi2`, `n_total`, `actual_power`; post hoc'ta `ncp`, `critical_chi2`, `power`.
- Hatada `isError: true` olur ve içerik CLI ile aynı `{"error", "code", "field"}` JSON'udur.

**Örnek çağrı ve sonuç**

```json
{"test": "chi2-contingency", "mode": "a-priori", "w": 0.3, "alpha": 0.05, "power": 0.95, "df": 5}
```
```json
{"ncp":19.8,"critical_chi2":11.070497693516355,"n_total":220,"actual_power":0.9502155018970163}
```

### CLI ↔ MCP eşdeğerlik testleri

| Test | Ne gösteriyor? |
|---|---|
| Sözleşmenin 25 açık referans vektörü | Her biri için MCP metni, CLI'nin stdout satırıyla **birebir** aynı. χ² vektörleri doğru sonucu; diğer dört aile, iki yüzde de aynı `UNSUPPORTED` hatasını veriyor. |
| SPEC'in 30 vektörü ve ek vektörler | Hesaplar, hata mesajları, kodlar ve alanlar iki yüzde de birebir aynı; `isError` CLI çıkış koduna karşılık geliyor. |
| Uçtan uca | Sunucu stdio üzerinden gerçek bir MCP istemcisiyle başlatılıyor; araç listesi, şema ve örnek çağrılar CLI ile karşılaştırılıyor. |
| İnce adaptör | MCP modülünde hesap kodu olmadığı kaynak düzeyinde denetleniyor. |

## AI ajanı (bonus katman)

Hekimin Türkçe klinik sorusunu, MCP aracını çağırarak yanıtlayan bir ajan. **Ajan hesap yapmaz.** Bütün sayılar motordan gelir; ajan yalnızca soruyu araç argümanlarına çevirir ve aracın sonucunu aktarır.

```
Hekimin Türkçe sorusu
  └─ Sistem 1   (claude-haiku-5-5; araç yok; çıktı yalnızca {"label", "confidence"})
       ├─ chi2-contingency ve güven ≥ 0.75  → MCP ajanı
       ├─ bilinen ama desteklenmeyen aile    → "bu araç desteklemiyor, araştırmacıya danışın"
       └─ ambiguous / unsupported / güven < 0.75 → "araştırmacıya sorun"
  └─ MCP ajanı  (claude-opus-5-5; tek araç: chi2_contingency_power)
       └─ MCP sunucusu → service.compute → engine
```

### Ajanın hesap yapmadığı nasıl güvence altında?

- Ajanın yerleşik araçlarının hepsi kapalı. Yalnızca gpower-clone MCP sunucusu bağlı ve izinli tek araç `chi2_contingency_power`. Kayıttaki `init` olayı bunu her çalıştırmada doğruluyor.
- Hekim "3×3 tablo" der. Ajan bunu `rows = 3, cols = 3` olarak iletir; df = (r − 1)(c − 1) hesabını **motor** yapar (`engine.df_from_table`).
- Cohen w eşlemesi (küçük 0,1 · orta 0,3 · büyük 0,5) bir hesap değil, bir sözlük eşlemesidir.
- Değerlendirme, ajanın son JSON satırındaki her sayıyı aracın döndürdüğü sayıyla birebir karşılaştırır. Ölçülen 10 soruda "ajan sayı üretti" bayrağı **0 kez** kalktı.

**Jev hakkında not.** Jev erişimimiz olmadığı için Sistem 1 adımında, yönergenin izin verdiği gibi **7 etiketle kısıtlanmış bir LLM** kullanıldı: `claude-haiku-5-5`, araçsız. Çıktısı bir JSON şemasıyla yalnızca etiket ve güvenle sınırlandı. Sistem 1 hiçbir sayı (N, güç, etki büyüklüğü) üretmez.

### Değerlendirme seti

[`tests/agent/eval_set.json`](tests/agent/eval_set.json) dosyasında 10 kurgusal Türkçe soru var; her birinin İngilizce çevirisi de dosyada. Sorular gerçek hasta verisi içermez.

| Soru grubu | Adet | Beklenen değerlerin kaynağı |
|---|---|---|
| χ² olumsallık soruları (4 a priori, 2 post hoc) | 6 | G\*Power oracle vektörleri: G-001, G-002, G-003, G-004, G-005, G-030 |
| Desteklenmeyen aileler (t2-indep, t-paired, anova-oneway) | 3 | Beklenen davranış: aileyi tanı, N üretme, araştırmacıya yönlendir. Belge amaçlı G\*Power referans değerleri ekran görüntüleriyle [`tests/agent/reference/`](tests/agent/reference/) altında: N = 210, 34, 159 (Q07'deki değer yönergedeki örnek çıktıyla aynı) |
| Belirsiz soru | 1 | Beklenen davranış: tahmin yapma, eksik bilgiyi sor (bilgi eksik olduğu için N belirlenemez) |

### Sonuçlar (Opus 5.5 / Haiku 5.5)

| Ölçüm | Sonuç |
|---|---|
| **Doğru seçim oranı** (test ailesi etiketi) | **10/10** |
| Doğru davranış (etiket + parametre + N/güç, ya da sayı vermeden yönlendirme) | **10/10** |
| χ² sorularında parametre / N / güç (7 ondalık) | 6/6 · 6/6 · 6/6 |
| "Ajan sayı üretti" | 0 |
| Sistem 1 etiket doğruluğu (her soru 3 tekrar) | **TR 30/30 · EN 30/30** |
| Sistem 1 kalibrasyonu | Güven 0.9–1.0: 56 tahmin, %100 doğru · 0.75–0.9: 4 tahmin, %100 doğru · <0.75: tahmin yok |

Ayrıntılı rapor [`tests/reports/agent_report.md`](tests/reports/agent_report.md) dosyasında: soru bazında tablo, kalibrasyon ve TR/EN karşılaştırması. Araç çağrı kayıtları da tutuluyor:

| Kayıt | İçerik |
|---|---|
| [`tests/reports/agent/main_runs.jsonl`](tests/reports/agent/main_runs.jsonl) | Her soru için araç çağrıları (ad, argüman, sonuç), son cevap, token ve süre |
| [`tests/reports/agent/system1_runs.jsonl`](tests/reports/agent/system1_runs.jsonl) | Sistem 1 çağrıları |
| [`tests/reports/agent/gui/`](tests/reports/agent/gui/) | GUI yolunun ham kayıtları |

**Önceki çalıştırma da raporda duruyor.** Makinedeki eski `claude` CLI'de `--model opus` ilk çalıştırmada Opus 4.8'e çözüldü. Bu çalıştırma raporda ayrı bir bölümde korunuyor:
- Etiket doğruluğu 10/10, davranış 9/10.
- Q03'te ajan doğru N'yi (964) aktardı, ama güç alanını boş bırakıp metne yaklaşık bir değer ("≈ 0,80") yazdı; değerlendirme bunu hata saydı.
- GUI yoluyla aynı modeli kullanmak için CLI güncellendi ve ölçüm Opus 5.5 ile tekrarlandı. Prompt ve puanlama tekrarda değiştirilmedi.

### MCP ↔ GUI karşılaştırması (ölçülmüş)

Aynı 10 soru iki yoldan da çözüldü; iki yolda da ana model **Opus 5.5**.
- **MCP yolu:** Ajan her soruyu ayrı bir `claude -p` çağrısında, MCP aracıyla çözdü.
- **GUI yolu:** Ayrı bir Claude Code oturumu G\*Power'ı bilgisayar kullanımıyla, ekran görüntüsü alıp tıklayarak kullandı. Token sayıları o oturumun kaydından, soru başına zaman pencerelerine göre ölçüldü.

| | MCP yolu | GUI yolu |
|---|---|---|
| Doğruluk | 10/10 | 10/10 |
| Token (yalnızca soru pencereleri) | **50 811** | **2 978 621** (≈ 59×) |
| Token (hazırlık ve kapanış dahil) | 50 811 | 3 746 372 (≈ 74×) |
| Süre (soru pencereleri) | 124 s | 130 s |
| Ekran görüntüsü | 0 | 16 (6 χ² sorusunda) |

**Adalet notu.**
- MCP yolunun her sorusu kendi başlangıç maliyetini taşır: süreç açılışı, sistem prompt'u, araç şeması. Süreleri de bu başlangıcı içerir.
- GUI yolu tek uzun bir konuşmadır: her model çağrısı birikmiş geçmişi ve ekran görüntülerini yeniden okur. Fark büyük ölçüde bu önbellek okumalarından gelir.
- GUI yolu, kapsam dışı ve belirsiz 4 soruda (Q07–Q10) G\*Power'ı hiç kullanmadı.
- Tam tablo ve yöntem: [`tests/reports/agent_report.md`](tests/reports/agent_report.md).

**Sonuç.** Hesap aynı, doğruluk aynı. Ama ekran görüntüsüyle çalışan bir ajan, aynı soruyu metin tabanlı bir araçla çözen ajana göre yaklaşık 60–75 kat daha fazla token harcıyor. Bu, yönergedeki "her arayüz bir maliyet transferidir" tezinin bu çalışmadaki ölçülmüş karşılığı.

## Ajanın söktüğü şeyin DOĞRU olduğunu nasıl kanıtladık?

Tek bir kanıta güvenmedik. Her iddia, birbirinden bağımsız katmanlardan geçti. Bir katman yanılırsa bir sonraki katmanın yakalaması gerekiyordu, ve nitekim yakaladı (bkz. 5. madde).

1. **Her iddia bir kanıta bağlı.** [`LEDGER.md`](LEDGER.md) kanıt defterinde 22 `[REA]` satırı var. Her biri bir fonksiyon adresine veya dize referansına, kısa bir alıntıya ve doğrulanabilir bir REA Evidence kimliğine bağlı. Örneğin hesap sınıfının adı (`PowerChiCont`) RTTI üzerinden, sabitler (0.5, 1.6, 1e-10) bayt düzeyinde okundu. Kanıtı gösterilemeyen her şey `[AJAN]` etiketiyle ayrıldı ve teste bağlandı. Evidence kimlikleri elle değil, REA çıktılarından bir betikle üretildi.
2. **Doğru cevabı ajan değil G\*Power belirliyor.** Beklenen değerler G\*Power arayüzünden toplanan 30 vektörden geliyor, hepsi ekran görüntülü ([`oracle/`](oracle/)). Vektörler binary'den çıkan kuralları zorlayacak şekilde seçildi: güç = α, w = 1e-6, kesirli df, N < 100 ve N > 100 dalları, 7 farklı hata mesajı. Binary'den okunan her hata mesajı, ekran görüntüsündeki metinle birebir karşılaştırıldı.
3. **Spec'i yazan ile kodu yazan farklı oturumlar (temiz oda).**
   - İnceleme oturumu yalnızca SPEC ve LEDGER üretti.
   - Yazım oturumu ayrı bir klasörde, ayrı bir git deposunda, **yalnızca SPEC.md ile** başladı; LEDGER'ı, Ghidra çıktılarını ve inceleme geçmişini hiç görmedi ([`prompts/`](prompts/)).
   - Yazım oturumu önce testleri yazdı (kırmızı commit), sonra kodu (yeşil commit); git geçmişinde bu sıra görülebilir.
   - Kod G\*Power'ı tutturuyorsa, bunun sebebi SPEC'in davranışı doğru anlatması olmalı; çünkü yazım oturumunun kopyalayabileceği başka bir kaynak yoktu.
4. **Bağımsız üçüncü bir hesap.** Aynı denklemi bağımsız olarak çözen statsmodels ile 894 vektör karşılaştırıldı. Uyuşmazlık çıkmadı.
5. **Ajanın hataları kayıt altında.** [`HALLUCINATIONS.md`](HALLUCINATIONS.md) dosyasında ajanın kendinden emin ama yanlış çıkardığı 3 iddia var; her birinin nasıl fark edildiği ve onu neyin yakaladığı yazılı:
   - **H-001:** Gerçek bir formül decompiler hatası sanıldı. Montaj (assembly) kontrolü yakaladı.
   - **H-002:** Evidence kimliklerinin sonu uyduruldu. Doğrulama betiği yakaladı.
   - **H-003:** Fonksiyona geçirilen bir sabit "tolerans" diye yorumlandı. Yazım oturumunun SPEC'e sorduğu soru yakaladı.

## Süreç

| Adım | Çıktı |
|---|---|
| Kurulum kontrolü | [`docs/setup-check.png`](docs/setup-check.png) |
| Oturum 1 · inceleme (REA + Ghidra) | [`LEDGER.md`](LEDGER.md) (22 `[REA]`, 4 `[DOK]`), [`SPEC.md`](SPEC.md) v1.2, ilk prompt [`prompts/session1-inspection.md`](prompts/session1-inspection.md) |
| Kâhin | [`oracle/vectors.csv`](oracle/vectors.csv) + 30 ekran görüntüsü |
| Oturum 2 · yazım (yalnızca SPEC) | `src/`, `tests/`, [`NOTES.md`](NOTES.md), ilk prompt [`prompts/session2-writing.md`](prompts/session2-writing.md) |
| SPEC geri bildirimi | Yazım oturumunun 4 sorusu SPEC v1.2 §5.1'de yanıtlandı ve koda uygulandı |
| Maliyet | [`AGENT_COST.md`](AGENT_COST.md) |

**Hangi dosyayı hangi oturum üretti?** Temiz oda kuralının işlediğini göstermek için:

| Oturum | Ürettikleri | Gördükleri |
|---|---|---|
| **Oturum 1 · inceleme** (REA + Ghidra) | `LEDGER.md` ve `SPEC.md`. Ayrıca kod olmayan belgeler ve veriler: `README.md`, `HALLUCINATIONS.md`, `AGENT_COST.md`, `oracle/vectors.csv` (G\*Power arayüz değerleri), `tests/agent/eval_set.json` (beklenen değerler G\*Power arayüzünden), GUI ölçüm dosyaları | Binary, REA/Ghidra çıktıları, G\*Power arayüzü |
| **Oturum 2 · yazım** (ayrı klasör, ayrı git deposu) | Bütün kod: `src/` ve `tests/` altındaki `.py` dosyaları, `pyproject.toml`, raporlar ve `NOTES.md` (NOTES.md'deki iki durum satırını sonradan inceleme oturumu güncelledi) | **Yalnızca** `SPEC.md`, sonra G\*Power arayüz değerleri (değerlendirme seti, GUI ölçümleri). Ghidra/REA çıktısı, LEDGER ya da inceleme geçmişi görmedi. |
| GUI yolu (ayrı oturum) | G\*Power'ı ekran görüntüsüyle kullanarak ölçüm (`tests/reports/agent/gui/`) | Yalnızca soru metinleri |

İnceleme oturumu hiçbir kod dosyası yazmadı. Kodun her satırı yazım oturumunun commit'lerinden geliyor (git geçmişinde "Oturum 2 … birleştirildi" commit'leri).

## Hedef binary

| Alan | Değer |
|---|---|
| Ürün | G\*Power 3.1.9.7 (Windows) |
| Kaynak | Resmi sayfa: https://www.psychologie.hhu.de/arbeitsgruppen/allgemeine-psychologie-und-arbeitspsychologie/gpower |
| Dağıtım dosyası | `GPowerWin_3.1.9.7.zip` — SHA-256 `3BB7F1F2478D74EE5BA701AE7F849373CF2B8A11F6B6216C7C6B236DB7861199` |
| İncelenen çalıştırılabilir | `GPowerNT.exe` (FileVersion 3.1.9.7) |
| `GPowerNT.exe` SHA-256 | `C63E6A133EB6372932F810C08CC33DC35A06D1DDB658F897BD6C34A754EFC812` |

> Not: Yönerge dosyayı "GPower.exe" diye anıyor; 3.1.9.7 Windows dağıtımında çalıştırılabilir dosyanın adı `GPowerNT.exe`.
> Binary bu repoda yer almaz (`.gitignore`). Ham decompile çıktıları da repoya konmadı; LEDGER'da yalnızca adres ve kısa alıntı var.

## Kurulum kontrolü

Ajana "REA araçları ve Ghidra sağlayıcısı bu oturumda kullanılabilir mi?" diye soruldu. Cevabı:

![Kurulum kontrolü](docs/setup-check.png)

| Araç | Sürüm |
|---|---|
| REA (`rea-agents`) | 6.5.0 (207 MCP aracı) |
| Ghidra | 12.1.4 (`ghidra_12.1.4_PUBLIC_20260921.zip`, SHA-256 `ddac49f9…87d2d4db`) |
| JDK | Eclipse Temurin 21.0.12.1 (64-bit) |
| Ajan | Claude Code (Opus 5.5) |
| `gpower-clone` | 0.1.0 (`pyproject.toml`) |
| Yeniden yazım | Python 3.14, scipy (dağılım fonksiyonları), statsmodels (yalnızca test) |

> **Windows + Claude masaüstü uygulaması notları**
> - Uygulama, MCP sunucularına sistem ortam değişkenlerini aktarmıyor. Bu yüzden `GHIDRA_INSTALL_DIR`, REA kaydının `env` alanına yazılmalı (`claude_desktop_config.json`).
> - İlk Ghidra analizi (~90 sn) MCP zaman aşımını aştı. Bu nedenle REA çağrıları CLI üzerinden yapıldı (`rea trace|function|read-bytes … --provider ghidra`).

## Kapsam

G\*Power'da: **Test family → χ² tests**, **Statistical test → Goodness-of-fit tests: Contingency tables**.

| Mod | Girdiler | Çıktılar |
|---|---|---|
| A priori (N hesapla) | w, α, güç, df | λ, kritik χ², df, toplam N, gerçek güç |
| Post hoc (güç hesapla) | w, α, toplam N, df | λ, kritik χ², df, güç |

Yönergedeki "eşit olmayan grup oranı" sınır değeri bu teste uygulanamaz: grup yoktur, yalnızca toplam N vardır (SPEC §1). Kılavuzda bu test için bölüm ya da çalışılmış örnek bulunmuyor (LEDGER L-032). Bu yüzden kâhin tamamen G\*Power arayüzünden toplandı.

## Repo yapısı

| Yol | İçerik |
|---|---|
| `SPEC.md` | Kanıttan çıkarılmış davranış belgesi, Gherkin kabul kriterleri |
| `LEDGER.md` | Kanıt defteri (`[DOK]` / `[REA]` / `[AJAN]`) ve tam Evidence dizini |
| `HALLUCINATIONS.md` | Ajanın yanlış çıkardıkları, nasıl fark edildikleri, onları yakalayan testler |
| `AGENT_COST.md` | Ajan, token, maliyet, iterasyon ve "neyi farklı yapardım" |
| `prompts/` | İki oturumun ilk prompt'ları |
| `oracle/` | G\*Power vektörleri (CSV) ve ekran görüntüleri |
| `src/gpower_clone/` | `engine.py` (hesabın tek yeri), `service.py` (CLI ve MCP'nin ortak katmanı), `cli.py` ve `mcp_server.py` (ince katmanlar), `agent/` (Sistem 1, MCP ajanı, değerlendirme) |
| `tests/` | Kabul, birim, CLI, MCP ve ajan testleri; diferansiyel test; statsmodels karşılaştırması; `tests/agent/eval_set.json`; `tests/reports/` uyum raporları, ajan raporu ve kayıtları |
| `NOTES.md` | Yazım oturumunun tasarım kararları ve SPEC'e soruları |

## Demo

▶️ **[Demo videosu (53 sn): `docs/demo.mp4`](docs/demo.mp4)**

Videoda sırasıyla şunlar var:
1. A priori hesap ve aynı girdilerle G\*Power'ın ekranı (N = 145).
2. Tablo boyutundan df ile hesap (3×3 → N = 133).
3. Post hoc güç.
4. Geçersiz girdi: G\*Power'ın mesajıyla birebir aynı hata ve sıfırdan farklı çıkış kodu.
5. Uyum raporu (30/30, KAPI %93,33).
6. Test paketi (187 test).
7. Türkçe soruyu MCP aracıyla yanıtlayan AI ajanı.

Video, bu komutların gerçek çalıştırma çıktılarından üretilmiş bir terminal kaydıdır. Test paketi (~2 dk) ve ajanın yanıtı (~15 sn) gibi bekleme süreleri kısaltılmıştır.

## Atıf

G\*Power, Franz Faul, Edgar Erdfelder, Albert-Georg Lang ve Axel Buchner tarafından geliştirilmiştir:

- Faul, F., Erdfelder, E., Lang, A.-G., & Buchner, A. (2007). G\*Power 3: A flexible statistical power analysis program for the social, behavioral, and biomedical sciences. *Behavior Research Methods, 39*, 175–191.
- Faul, F., Erdfelder, E., Buchner, A., & Lang, A.-G. (2009). Statistical power analyses using G\*Power 3.1: Tests for correlation and regression analyses. *Behavior Research Methods, 41*, 1149–1160.

Bu çalışma eğitim amacıyla yapılmıştır. G\*Power yalnızca resmi sayfasından dağıtılır; bu repo G\*Power'ın hiçbir dosyasını içermez.
