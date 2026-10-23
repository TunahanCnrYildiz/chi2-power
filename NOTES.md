# NOTES — gpower-clone (χ² olumsallık tablosu, temiz oda yazımı)

Tek davranış kaynağı: `SPEC.md` (şu an v2.0; §0 = eğitmenin arayüz sözleşmesi v1.0.0, öncelikli). Başka kaynak
açılmadı; tersine mühendislik aracı kullanılmadı.

## Kurulum ve çalıştırma

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[test,diff,mcp]"     # Linux/macOS: .venv/bin/python
```

```bash
gpower-clone --test chi2-contingency --mode a-priori --w 0.3 --alpha 0.05 --power 0.95 --df 1
# {"ncp":13.049999999999999,"critical_chi2":3.8414588206941285,"n_total":145,"actual_power":0.9507851454132252}
gpower-clone --test chi2-contingency --mode post-hoc --w 0.3 --alpha 0.05 --n_total 100 --df 1
# {"ncp":9.0,"critical_chi2":3.8414588206941285,"power":0.850838768327056}
gpower-clone --version
# {"contract_version":"1.0.0","name":"chi2-power","engine":"Python 3.14.6, scipy 1.18.1"}
```

Testler ve raporlar:

```bash
.venv/Scripts/python -m pytest -q
.venv/Scripts/python tests/differential.py
.venv/Scripts/python tests/differential.py --csv tests/fixtures/spec_vectors.csv --report tests/reports/differential_report_spec.md
.venv/Scripts/python tests/statsmodels_vectors.py
```

- `pytest -q`: kabul, sözleşme, birim, CLI, MCP ve düzenek testlerini çalıştırır.
- `differential.py` (bağımsız): `oracle/vectors.csv` ile karşılaştırır, raporu `tests/reports/differential_report.md`
  dosyasına yazar.
- `differential.py --csv …`: aynı karşılaştırmayı SPEC vektörleriyle yapar.
- `statsmodels_vectors.py`: raporu `tests/reports/statsmodels_report.md`, vektörleri `statsmodels_vectors.csv`
  dosyasına yazar.

`differential.py` çıkış kodu: KAPI geçerse 0, geçmezse 1, CSV yoksa 2. `--cmd "gpower-clone"` ile başka bir komut denenebilir.

## Yapı

| Dosya | Görev |
|---|---|
| `src/gpower_clone/engine.py` | Hesap ve alan kuralları (§2.1 sırası, §2.2 mesajları, §0.5 sözleşme aralıkları), §4 formülleri (scipy), §4.5 N araması |
| `src/gpower_clone/service.py` | Ortak katman (sözleşme §0): alan kümesi, doğrulama sırası, tür denetimi, hata kodları, çıktı alanları, sürüm |
| `src/gpower_clone/cli.py` | İnce katman: `--alan değer` ayrıştırma → `service.compute` → tek satır JSON, çıkış kodu |
| `src/gpower_clone/mcp_server.py` | MCP sunucusu (stdio): tek araç `power_analysis`, ham argümanları `service.compute`'a verir |
| `tests/test_contract.py` | Sözleşme v1.0.0: açık vektörler, sürüm, hata kodu/alan/çıkış kodu, aralıklar, süre |
| `tests/test_acceptance.py` | SPEC §6 Gherkin (sözleşme alan adlarıyla, 1e-6 tolerans); G-019/G-023/G-025 sözleşme hatası |
| `tests/test_engine.py`, `tests/test_cli.py` | §4.5 adımları, sınırlar, kod/alan, rows/cols uzantısı, alt süreç (`python -m`, console script) |
| `tests/differential.py` | `oracle/vectors.csv` ↔ CLI (gerçek alt süreç), §0.6 toleransı, sözleşme farkları ayrı, süre ölçümü |
| `tests/fixtures/spec_vectors.csv` | SPEC §6'daki 30 vektörün CSV biçimi (düzeneği kâhin gelmeden sınamak için) |
| `tests/fixtures/public_vectors.jsonl` | Sözleşmenin 25 açık referans vektörü (eğitmen) |
| `tests/statsmodels_vectors.py`, `tests/test_statsmodels.py` | statsmodels `GofChisquarePower` ile 894 vektör |
| `tests/test_mcp.py` | MCP ↔ CLI birebir aynı metin (25 açık + 30 SPEC + 11 ek vektör), stdio uçtan uca, ince adaptör |
| `src/gpower_clone/agent/`, `tests/test_agent.py` | AI ajanı (Sistem 1, MCP ajanı, puanlama, değerlendirme, GUI karşılaştırması) |
| `tests/reports/` | Üretilen uyum raporları |

## Sözleşme uyumu (arayüz sözleşmesi v1.0.0, SPEC §0)

Hesap motoru değişmedi; değişen arayüzdür. Bütün arayüz kuralları `service.py` içinde tek yerde. CLI ve MCP
aynı ham alan sözlüğünü buraya verir.

| Konu | Uygulama |
|---|---|
| Alanlar (§0.1) | a priori `w, alpha, power, df`; post hoc `w, alpha, n_total, df`. Tek uzantı: `df` yerine `rows` + `cols` (df'yi `engine.df_from_table` hesaplar; ikisi birden verilip tutarsızsa `INCONSISTENT`/`df`). |
| Ayrıştırma | `--alan değer` ya da `--alan=değer`. Değer `-` ile başlayabilir (`--w -0.1`). Ondalık ayırıcı noktadır; `0,3`, `nan`, `inf` → `INVALID_VALUE`. |
| Çıktı (§0.2) | a priori `ncp, critical_chi2, n_total, actual_power`; post hoc `ncp, critical_chi2, power`. `df` yok. stdout'ta yalnızca tek satır JSON; uyarılar stderr'e. |
| Sürüm (§0.3) | `gpower-clone --version` → `{"contract_version":"1.0.0","name":"chi2-power","engine":"Python …, scipy …"}`, çıkış 0. |
| Hata (§0.4) | `{"error","code","field"}`. Çıkış kodu girdi hatasında **2**, iç hatada ve `NO_SOLUTION`'da **1**. `error` metni mümkünse G*Power mesajıdır (§2.2). |
| Doğrulama sırası | test → mode → tanınmayan/ilgisiz alan → eksik alan → tür (df, rows, cols, w, alpha, power/n_total) → alan kuralları (§2.1 sırası, motorda). |
| Aralıklar (§0.5) | `w > 0` (post hoc w = 0 → `OUT_OF_RANGE`), `n_total` tam sayı ≥ 2 (N = 1 → `OUT_OF_RANGE`), `df` tam sayı ≥ 1 (2.5 → `INVALID_VALUE`). G*Power'ın daha dar aralıkları (α, güç ∈ [1e-7, 0.9999999], a priori w ≥ 1e-6) ve mesajları korunur. |
| χ² dışı aileler | `UNSUPPORTED`/`test`. 25 açık vektörün 20'si bu durumda; CLI ve MCP aynı hatayı verir. |
| MCP (§0.8) | Tek araç `power_analysis`; `test` ve `mode` zorunlu, alan adları CLI ile aynı. Metin içeriği CLI'nin stdout satırıyla birebir aynı; hata `isError = true`. |

**Kod eşlemesi**

| Durum | `code` | `field` | Örnek `error` |
|---|---|---|---|
| test/mode eksik | `MISSING_PARAM` | `test`/`mode` | `Missing required parameter: mode` |
| Moda gereken alan eksik | `MISSING_PARAM` | alan | `Missing required parameter: df (or rows and cols)` |
| Bilinmeyen alan (`--n`, `--n-total`, `--tails`, `--ratio`, …) | `UNKNOWN_PARAM` | alan | `Unknown parameter: tails` |
| Modla ilgisiz alan (post hoc'ta `--power`) | `UNKNOWN_PARAM` | alan | `Parameter power is not used in mode post-hoc` |
| Sayı değil, NaN/∞, tam sayı alanında ondalık | `INVALID_VALUE` | alan | `Invalid value for df: 2.5 (must be an integer)` |
| G*Power ya da sözleşme aralığı dışında | `OUT_OF_RANGE` | alan | G*Power mesajı (ör. `Degrees of Freedom must be greater or equal one.`) |
| güç < α | `INCONSISTENT` | `power` | `Power must be greater than or equal to alpha.` |
| df ile rows/cols tutarsız | `INCONSISTENT` | `df` | `Inconsistent parameters: df 2 does not match (rows - 1) * (cols - 1) = 4` |
| Bilinmeyen test ya da mode (`posthoc` dahil) | `UNSUPPORTED` | `test`/`mode` | `Unsupported test: t2-indep (supported: chi2-contingency)` |
| Aralık genişletmede taşma | `NO_SOLUTION` | null | `Unable to bracket the total sample size (upper bound overflow).` (çıkış 1) |
| Beklenmeyen durum | `INTERNAL_ERROR` | null | çıkış 1 (kod adı tasarım kararı; tabloda yok) |

**Sözleşmeyle kalkan ya da değişen eski kararlar**

| Eski karar | Durum |
|---|---|
| Eş adlar `--n`, `--n-total`, `--n_total` (N için), `--mode posthoc` | **Kalktı.** N'nin tek adı `n_total`; diğerleri `UNKNOWN_PARAM`, `posthoc` `UNSUPPORTED`/`mode`. |
| S-4: `--tails`, `--ratio` ve moda ait olmayan parametreler yok sayılır | **Kalktı.** Hepsi `UNKNOWN_PARAM`. |
| S-3: çıktıda df, tamsayıysa `1`, değilse `2.5` | **Kalktı.** df artık çıktı değil. |
| Hata `{"error"}`, çıkış kodu 1 (girdi) / 2 (iç) | **Değişti.** `{"error","code","field"}`, girdi 2, iç 1. |
| Kesirli df kabul (G-019), post hoc w = 0 (G-023), N = 1 (G-025) | **Değişti.** Sözleşme gereği reddedilir. Motorda `contract=False` ile G*Power davranışı korunuyor ve testleniyor. |
| A-3: kesirli N → `Total sample size must be an integer.` | Mesaj aynı, kod `INVALID_VALUE`/`n_total`. Tür aşamasında yakalanır. |
| Ayrıştırma ve eksik parametre mesajları (S-2) | Yine tasarım kararı. Bayrak adıyla değil alan adıyla yazılıyor (`power`, `--power` değil), çünkü CLI ile MCP'nin metni birebir aynı olmalı. |

**Yeni tasarım kararları:**
- Tam sayı alanlarında tam sayı değerli ondalık yazımlar (`100.0`, `1e2`) kabul edilir.
- Aynı alan iki kez verilirse `INVALID_VALUE` döner.
- `--` ile başlamayan fazladan bir argüman `UNKNOWN_PARAM` döner (alan: o argüman).
- Değersiz bayrak (`--df` sonda) `INVALID_VALUE` döner.
- Bu ayrıştırma hataları test/mode denetiminden önce yakalanır.

**Süre (§0.1, 2 s sınırı)**
- Alt süreç olarak sıcak çağrı 0.85–0.88 s (30 SPEC vektörü, `differential_report_spec.md`). Ölçüm: boş Python 0.03 s,
  scipy.stats importuyla 0.85 s; sürenin neredeyse tamamı scipy.stats importu. Bütün testlerde her çağrı 2 s'nin altında.
- **Soğuk başlangıç:** Bilgisayar açıldıktan ya da Python/scipy güncellendikten sonraki ilk çağrıda dosya
  önbelleği boşken scipy.stats importu bir kez **10.7 s** ölçüldü (`-X importtime`). Bu, sonraki çağrılarda
  tekrarlanmadı. Değerlendirme düzeneği soğuk diskte ilk çağrıyı yaparsa 2 s'yi aşabilir. Önlem olarak sınavdan
  önce bir kez `gpower-clone --version` ya da bir hesap çalıştırmak yeterli.

## Sonuçlar

- pytest: **266 geçti, 1 atlandı** (`oracle/vectors.csv` henüz yok → `test_oracle_gate` atlanıyor)**
- **SPEC vektörleri** (`tests/reports/differential_report_spec.md`, §0.6 toleransı):
  - 30/30 vektör beklenen sonucu veriyor: 20 hesap, 7 G*Power hatası (mesaj, kod ve alan), 3 sözleşme farkı.
  - **KAPI: 13/14 = %92.86.** Payda yalnızca a priori `n_total` vektörlerinden oluşuyor; G-019 hariç tutuldu,
    G-013 doğrulanamayan sayıldı. Doğrulanabilir vektörlerde oran %100; eşik %90 → GEÇTİ.
  - KAPI'nin paydası küçüldü (eski 23), çünkü post hoc'ta `n_total` artık çıktı değil.
  - Kâhin CSV'si gelince aynı betik onunla tekrar çalıştırılmalı.
- **Açık referans vektörleri** (`tests/fixtures/public_vectors.jsonl`):
  - χ² a priori: N = 220, güç 0.9502155.
  - χ² post hoc: güç 0.6235846.
  - İkisi de 1e-6 toleransla tutuyor.
  - Diğer 20 vektör (t2-indep, t-paired, anova-oneway, multireg-r2) `UNSUPPORTED`/`test` veriyor.
  - Bonus modlar (compromise, criterion, sensitivity) Aşama 1'de `UNSUPPORTED`/`mode` veriyor; Aşama 2'de eklenecek.
- **statsmodels** (`tests/reports/statsmodels_report.md`):
  - 594/594 a priori vektörde `n_total = ⌈N_sm⌉`.
  - 594/594 minimallik: güç(n_total) ≥ hedef ve güç(n_total − 1) < hedef.
  - 300/300 post hoc güç 7 ondalıkta eşit.
  - R `pwr` makinede kurulu olmadığı için kullanılmadı.

### Kesirli N ↔ tamsayı N ilişkisi (SPEC §4.5/4)

statsmodels ve gpower-clone aynı sürekli denklemi (güç(w, α, N) = hedef) çözer. statsmodels kökü kesirli döndürür.
gpower-clone ise kökü 10 ondalığa yuvarlar (⌊N·10¹⁰ + 0.5⌋/10¹⁰), sonra yukarı yuvarlar; sonuç aralığın alt
ucundan küçükse alt uca çeker (§4.5/5). Güç N'de arttığından bu, hedefe ulaşan en küçük tamsayıdır ve ⌈N_sm⌉'e eşittir.

İki sonuç ancak kök bir tamsayıya çok yakınsa ayrılabilir. İki sebebi var:
- Kesir 5·10⁻¹¹'den küçükse G*Power kuralı aşağı yuvarlar (104.00000000003 → 104).
- İki çözücünün toleransı farklıdır.

Ölçümler:
- Izgarada kesirli kökler arasındaki en büyük fark 2.5·10⁻⁶ (göreli 2.5·10⁻⁷).
- Kökteki artık gpower-clone'da 5.6·10⁻¹⁶ (v1.2 durma ölçütüyle; önce 1.5·10⁻¹²), statsmodels'te 8.5·10⁻⁸.
  Yani fark statsmodels çözücüsünün gevşek toleransından geliyor.
- Hiçbir kök bir tamsayıya 10⁻⁶'dan yakın değildi; bu yüzden bu ızgarada kural farkı ortaya çıkmadı.

## MCP sunucusu (bonus katman)

Motorun önünde ince bir adaptör. Akış: `mcp_server` (`power_analysis`) → `service.compute` → `engine`.
- CLI de aynı `service.compute` ve `service.to_json` fonksiyonlarını kullanır.
- MCP modülünde scipy, `math`, sayı dönüştürme ya da ayrıştırma yoktur.
- SDK: resmi Python `mcp` 2.3.0 (`mcp.server.mcpserver.MCPServer`); taşıma stdio.

**Ham argüman tasarım kararı:** SDK, şemada olmayan alanları sessizce atar. Bu yüzden sunucu `call_tool` metodunu
ezer ve araç argümanlarını hiç dönüştürmeden `service.compute`'a verir. Sonuçlar:
- Şemada olmayan bir alan (ör. `tails`) CLI'deki gibi `UNKNOWN_PARAM` olur.
- Sayı yerine metin (`"abc"`) CLI'deki gibi `INVALID_VALUE` olur.
- Kayıtlı fonksiyon yalnızca girdi şemasını ve belgeyi üretir.

### Kurulum ve çalıştırma

```bash
.venv/Scripts/python -m pip install -e ".[mcp]"
```

```bash
gpower-clone-mcp
```

`python -m gpower_clone.mcp_server` de aynı sunucuyu başlatır. Sunucu stdin/stdout üzerinden konuşur; elle
çalıştırıldığında istemci bekler.

### Kayıt örnekleri

Claude Code:

```bash
claude mcp add gpower-clone -- "D:/Claude Projects/Teardown Sprint - Yazim/.venv/Scripts/gpower-clone-mcp.exe"
```

Claude Desktop (`claude_desktop_config.json`) ya da proje kökündeki `.mcp.json`:

```json
{
  "mcpServers": {
    "gpower-clone": {
      "command": "D:/Claude Projects/Teardown Sprint - Yazim/.venv/Scripts/gpower-clone-mcp.exe",
      "args": []
    }
  }
}
```

### Araç: `power_analysis`

Girdi şeması (alan adları CLI ile aynı):

| Alan | Tip | Zorunlu | Açıklama (şemadaki metin) |
|---|---|---|---|
| `test` | string | evet | Test family; only chi2-contingency is supported |
| `mode` | `"a-priori"` \| `"post-hoc"` | evet | a-priori: solve n_total; post-hoc: solve power |
| `w` | number | mod gereği | Effect size w > 0 (a-priori: >= 1e-6) |
| `alpha` | number | mod gereği | Alpha, 1e-7..0.9999999 |
| `power` | number | a priori | a-priori only: target power, 1e-7..0.9999999, >= alpha |
| `n_total` | integer | post hoc | post-hoc only: total N, 2..2147483646 |
| `df` | integer | df ya da rows+cols | Degrees of freedom, integer >= 1; or give rows+cols |
| `rows`, `cols` | integer | uzantı | Table rows/columns >= 2 (df computed by the engine) |

Sonuç:
- Tek metin içeriği, CLI'nin stdout satırıyla birebir aynı JSON'dur. `structuredContent` aynı sözlüktür.
- Başarıda çıktı alanları CLI ile aynıdır (§0.2).
- Hatada `isError = true` ve içerik `{"error","code","field"}` olur.

### Test sonuçları (`tests/test_mcp.py`)

- (a) Süreç içi: metin içeriği her vektörde CLI alt süreç satırıyla **birebir aynı**; `isError` CLI çıkış koduna
  karşılık geliyor. Kapsam:
  - 25 açık referans vektörünün her biri; χ² dışındaki 20'si iki tarafta da `UNSUPPORTED` veriyor.
  - 30 SPEC vektörü.
  - 11 ek durum: rows/cols, tutarsız df, ilgisiz alan, bilinmeyen alan, metin değer, kesirli df, `posthoc`,
    eksik test ve eksik mode.
- (b) Uçtan uca: sunucu `python -m gpower_clone.mcp_server` olarak stdio üzerinden gerçek `mcp.Client` ile başlatılıyor.
  Araç listesi (`power_analysis`) ve şema (zorunlu: `test`, `mode`) doğrulanıyor; 4 vektör CLI ile aynı.
- (c) İnce adaptör: `mcp_server.py` kaynağında scipy, `chi2.`, `ncx2`, `math`, `float(`, `int(` ve motor
  fonksiyonları geçmiyor. CLI de motoru doğrudan içe aktarmıyor.

## AI ajanı (bonus katman)

### Mimari

```
Hekimin Türkçe sorusu
  └─ Sistem 1  (claude -p --model claude-haiku-5-5; araç yok; --json-schema → yalnızca {"label", "confidence"})
       ├─ chi2-contingency ve confidence ≥ 0.75 → MCP ajanı
       ├─ bilinen ama desteklenmeyen aile (t2-indep, t-paired, anova-oneway, multireg-r2) → "desteklenmiyor, araştırmacıya danışın"
       └─ ambiguous / unsupported ya da confidence < 0.75 → "araştırmacıya sorun"
  └─ MCP ajanı (claude -p --model claude-opus-5-5; tek araç mcp__gpower-clone__chi2_contingency_power)
       └─ gpower-clone MCP sunucusu → service.compute → engine (bütün sayılar buradan)
```

- **Ajan hesap yapmaz.** Yerleşik araçların hepsi kapalı (`--tools ""`). Yalnızca gpower-clone MCP sunucusu
  bağlanıyor (`--mcp-config` + `--strict-mcp-config`); izinli tek araç `--allowedTools mcp__gpower-clone__chi2_contingency_power`,
  izin kipi `--permission-mode dontAsk` (izinsiz her şey reddedilir). `init` olayındaki araç listesi kayıtta
  saklanıyor ve gerçek çalıştırmalarda yalnızca bu aracı içeriyor.
- **Tablo boyutundan df:** Hekim "3×3" der. Ajan bunu `rows = 3, cols = 3` olarak iletir; df = (r − 1)(c − 1)
  hesabını motordaki `engine.df_from_table` yapar. Tamsayılık ve ≥ 2 doğrulaması da orada. `service` katmanı df ile
  rows/cols'un ikisini birden kabul eder, tutarsızlıkta hata verir. CLI'de `--rows/--cols`, MCP aracında `rows/cols` var.
- **Sistem prompt'u** ([prompts.py](src/gpower_clone/agent/prompts.py)), Türkçe kurallar:
  - Sayıyı asla kendin hesaplama; metne türetilmiş sayı da yazma.
  - Cohen w eşlemesi: küçük 0,1, orta 0,3, büyük 0,5.
  - Tablo boyutunu rows/cols olarak ilet.
  - Desteklenmeyen ailede N üretme, araştırmacıya yönlendir.
  - Bilgi eksikse sor.
  - Cevabın son satırı `{"label", "n_total", "actual_power"}` JSON'u olsun.
- **Jev yerine:** Jev erişimi olmadığından Sistem 1 için ödevin izin verdiği "etiket setine kısıtlı LLM" kullanıldı:
  `claude -p --model claude-haiku-5-5`, araçsız. Çıktı JSON şemasıyla (`additionalProperties: false`, etiket `enum`)
  `{"label", "confidence"}` ile sınırlı; şema dışı alan içeren bir çıktı geçersiz sayılıyor.

### Çalıştırma

Ön koşul: `claude` CLI'de abonelik girişi (`claude auth login`; `claude auth status` → `"subscriptionType": "pro"`).
API anahtarı kullanılmaz; alt süreçten `ANTHROPIC_API_KEY` bilerek çıkarılıyor.

```bash
gpower-clone-agent "3×3 tabloda orta etki, α = 0,05 ve %80 güç için toplam kaç hasta gerekir?"
```

```bash
.venv/Scripts/python -m gpower_clone.agent.evaluate
```

```bash
.venv/Scripts/python -m gpower_clone.agent.evaluate --report-only
```

İlk komut boru hattını tek soruda çalıştırır. İkincisi tam değerlendirmedir: 10 soru için ana ajan, ayrıca Sistem 1
TR/EN × 3 tekrar. Kayıtlar `tests/reports/agent/*.jsonl` dosyalarına, rapor `tests/reports/agent_report.md`
dosyasına yazılır. Üçüncüsü raporu kayıtlardan yeniden üretir; GUI sonuçları gelince bunu çalıştırmak yeterlidir.

### Tasarım kararları

1. **Alt süreç ortamı.** Ajan, Claude Code masaüstü oturumunun içinden başlatıldığında `CLAUDE_CODE_*`,
   `ANTHROPIC_BASE_URL` gibi değişkenleri devralıyor ve "giriş yapılmamış" ya da bare kipe düşüyordu. Bu değişkenler
   ve `ANTHROPIC_API_KEY` alt süreçten çıkarılıyor (`claude_cli.child_env`).
2. **MCP bağlantısını bekleme.** `-p` kipinde MCP sunucusu varsayılan olarak beklenmiyor: ilk denemede `init`
   olayında sunucu `pending`, araç listesi boştu ve model aracı göremedi. `MCP_CONNECTION_NONBLOCKING=false`,
   `MCP_TIMEOUT=60000` ile bağlantı bekleniyor. Bu deneme çalıştırması değerlendirmeye dahil değil.
3. **Yalıtım.** `--setting-sources ""`, `--disable-slash-commands`, `--no-session-persistence` kullanılıyor ve
   çalışma dizini boş bir geçici klasör. Böylece kullanıcının hook'ları, eklentileri ve proje dosyaları bağlama girmiyor.
4. **Token ölçümü.** `claude` JSON çıktısındaki `modelUsage` alanı toplanıyor: bütün modeller ve bütün turlar.
   Claude Code ana modelin yanında arka planda küçük bir modelle (Haiku) de çağrı yapıyor; bu çağrılar da sayılıyor.
   Ham `usage` ve `modelUsage` kayıtta ayrıca duruyor.
5. **"Ajan sayı üretti" kontrolü.** JSON satırındaki `n_total` ve `actual_power`, son başarılı araç sonucundaki
   değerlerle birebir (`==`) karşılaştırılıyor. Araç çağrısı yoksa ya da değer farklıysa soru işaretleniyor.
   Ek bir bilgi amaçlı kontrol, metinde soruda, araç argümanlarında ya da araç sonucunda karşılığı olmayan
   sayıları listeliyor. Bu kontrol, deneme çalıştırmasında modelin kendiliğinden yazdığı "hücre başına ~36 kişi"
   gibi durumlar için eklendi.
6. **Puanlama.** χ² sorularında "doğru" için şunların hepsi gerekir:
   - etiket doğru;
   - araç argümanları beklenenle aynı (mode, w, α, güç ya da n; df ya da rows/cols'tan elde edilen df);
   - N birebir aynı;
   - güç 7 ondalıkta G\*Power ile aynı.

   Desteklenmeyen ve belirsiz sorularda "doğru" için şunlar gerekir:
   - etiket doğru;
   - JSON'da sayı yok;
   - başarılı araç çağrısı yok.

   Sistem 1'de yönlendirmenin doğru sayılması:
   - χ² sorusu → ajana geçmeli;
   - bilinen ama desteklenmeyen aile → "yönlendir" ya da "sor" (ikisinde de N üretilmez);
   - belirsiz soru → yalnızca "sor".
7. **Kalibrasyon aralıkları:** 0.9–1.0, 0.75–0.9 (yönlendirme eşiği) ve < 0.75.
8. **Açık model kimlikleri.** `opus` ve `haiku` takma adları CLI sürümüne göre farklı modellere çözülebildiği için ana ajanda ve Sistem 1'de varsayılan olarak açık kimlikler kullanılır: `claude-opus-5-5` ve `claude-haiku-5-5`. `--main-model` ve `--s1-model` ile değiştirilebilir. Raporda ana sonuç, en son çalıştırılan modelin kayıtlarıdır; önceki modellerin kayıtları silinmez ve "Önceki çalıştırma" alt bölümlerinde özetlenir.

### Sonuçlar

Ölçüm 2026-10-18, abonelik girişiyle (Pro). İki tur yapıldı; ikisinin kaydı da
`tests/reports/agent/main_runs.jsonl` ve `system1_runs.jsonl` dosyalarında duruyor. Bu kayıtlarda araç adı,
argümanlar, sonuç, son cevap, süre ve token var. Ayrıntılı rapor: [tests/reports/agent_report.md](tests/reports/agent_report.md).

1. **Tur 1 (önceki):** `--model opus` ve `--model haiku` takma adlarıyla çalıştırıldı. claude CLI 2.1.211 bu adları
   `claude-opus-4-8` ve `claude-haiku-4-5` modellerine çözdü. GUI yolu ise Opus 5.5 ile koşmuştu, yani karşılaştırma
   adil değildi.
2. **Tur 2 (ana sonuç):** Modeller açık kimlikle verildi: `--model claude-opus-5-5`, `--model claude-haiku-5-5`.
   CLI 2.1.211 Opus 5.5'i reddetti ("version 2.1.280 or newer is required"). Kullanıcının izniyle `claude update`
   çalıştırıldı ve CLI 2.1.302'ye güncellendi. Bu sürümde iki kimlik de kabul ediliyor; JSON çıktısındaki model
   alanında `claude-opus-5-5` ve `claude-haiku-5-5` görünüyor.

Toplam çağrı sayısı **140**: her turda 10 ana ajan ve 60 Sistem 1 çağrısı. Bunlara değerlendirmeye girmeyen
6 doğrulama ve hata ayıklama çağrısı (biri CLI tarafından reddedildi) ekleniyor. Prompt ve puanlama iki turda aynı.

**Ana ajan (MCP yolu)**

| Ölçüt | Tur 2: claude-opus-5-5 | Tur 1: claude-opus-4-8 |
|---|---|---|
| Doğru seçim oranı (etiket, 10 soru) | **10/10** | 10/10 |
| Doğru davranış | **10/10** | 9/10 (Q03) |
| χ² sorularında parametre / N / güç (7 ondalık) | 6/6 / 6/6 / 6/6 | 6/6 / 6/6 / 5/6 |
| "Ajan sayı üretti" bayrağı | 0 | 0 |
| Token (10 soru, tüm modeller) | 50 811 | 47 126 |
| Süre (duvar saati) | 124.0 s | 88.6 s |

- **Araç erişimi.** İki turda da ajanın gördüğü tek araç `mcp__gpower-clone__chi2_contingency_power` oldu
  (`init` olayından).
- **Q03.** Tur 1'de Opus 4.8 JSON satırında `actual_power` alanını boş (`null`) bırakmıştı. Tur 2'de Opus 5.5 bu
  alanı araç sonucunun bütün basamaklarıyla doldurdu. Puanlama değiştirilmedi; iki sonuç da olduğu gibi raporlandı.
- **Q06 süresi.** Tur 2'de Q06 31.5 s sürdü; API süresi de 28.7 s. Bu yüzden yavaşlık süreç başlatmadan değil,
  model tarafından.
- **Bilgi amaçlı metin kontrolü.** Kontrol bazı sayıları gösteriyor: Q05'te "%80" ve Q08'de "d = 0,5" gibi
  açıklamalar; Q10'da madde numaraları ve yaygın α/güç önerileri. Bunlar hesap sonucu değil; JSON satırlarında
  araç dışı sayı yok.

**Sistem 1** (10 soru × TR/EN × 3 tekrar = 60 çağrı; geçersiz çıktı 0)

| | Tur 2: claude-haiku-5-5 TR | EN | Tur 1: claude-haiku-4-5 TR | EN |
|---|---|---|---|---|
| Etiket doğruluğu | **30/30** | **30/30** | 29/30 | 28/30 |
| Yönlendirme doğruluğu | 30/30 | 30/30 | 30/30 | 30/30 |
| Ortalama güven | 0.93 | 0.94 | 0.96 | 0.97 |

- **Kalibrasyon, Tur 2.** 0.9–1.0 aralığındaki 56 tahminin hepsi doğru; 0.75–0.9 aralığındaki 4 tahminin de
  hepsi doğru. Bu 4 tahminin hepsi belirsiz soru Q10'a ait, güven 0.85–0.90. Yani model belirsiz soruda güvenini
  makul biçimde düşürüyor.
- **Kalibrasyon, Tur 1.** Haiku 4.5, Q10'u İngilizcede iki kez 0.95 güvenle `unsupported` olarak etiketlemişti;
  İngilizcede güven biraz fazlaydı.
- **İki dil.** Tur 2'de Türkçe ile İngilizce arasında doğrulukta fark yok.

**MCP ↔ GUI** (ana sonuç Tur 2; GUI ölçümleri `gui_results.json` ve `gui_overhead.json` dosyalarından okundu,
değiştirilmedi; iki yolda da ana model Opus 5.5)

| | MCP (claude-opus-5-5) | GUI (Opus 5.5) |
|---|---|---|
| Token (yalnızca soru pencereleri) | 50 811 | 2 978 621 (59×) |
| Token (hazırlık ve kapanış dahil) | 50 811 | 3 746 372 (74×) |
| Süre | 124.0 s | 129.8 s |
| Doğruluk | 10/10 | 10/10 |
| Ekran görüntüsü | 0 | 16 |

- **Adalet notu** (raporda da var):
  - MCP yolunda her soru ayrı bir süreçte, kendi başlangıç maliyetiyle çözüldü.
  - GUI yolu tek uzun bir konuşmaydı ve birikmiş geçmişi ile ekran görüntülerini yeniden okudu.
  - GUI, Q07–Q10'da kullanılmadı.
- **Süre karşılaştırması.** İki yolun süresi yakın, çünkü MCP süresine süreç başlatma ve MCP sunucusunun açılışı
  dahil.
- **Token farkı.** Fark büyük ölçüde GUI'nin önbellekten yeniden okuduğu bağlamdan geliyor.

## SPEC v1.2 ile değişenler

| Eski karar | v1.2 durumu |
|---|---|
| 1. G-007'de kök bulunamazsa N = alt, yoksa uydurma hata `Unable to find a total sample size…` | **Kalktı.** §4.5/3: uçlar aynı işaretliyse kök bulucu **0** döndürür; §4.5/5: n_total < alt ise n_total = alt ve yeniden yuvarlanır. G-007: 0 → 0 → alt = 1. Uydurma mesaj silindi. |
| 2. Brent durma ölçütü tol1 = 2·eps·\|b\| + 0.5·1e-10; 300 iterasyonda hata | **Değişti.** \|yarım aralık\| ≤ 1.1102230246251565e-16·\|b\| ya da f(b) = 0; 300 iterasyon dolarsa son tahmin b döner, hata yok. 894 statsmodels vektöründe hiçbir `n_total`/`actual_power` değişmedi (kesirli N en çok 2.5·10⁻¹¹ kaydı; `tests/test_statsmodels.py`). |
| 3. Aralık genişletmede taşma → uydurma hata | **Kaldı** (SPEC §5.1 S-1 serbest bırakıyor); mesaj `Unable to bracket the total sample size (upper bound overflow).` Pratikte erişilemez. |
| `round_n` içinde "en az 1" | **Değişti.** Alt sınır artık §4.5/5'teki alt uç kuralıyla uygulanıyor (alt ≥ 1). |
| 9. `df` her zaman ondalık (`1.0`) | **Değişti** (S-3): tamsayıya eşitse `1`, değilse `2.5`. |
| 7. Moda ait olmayan bilinen parametre yok sayılır | **Kaldı** (S-4); ayrıca `--tails` ve `--ratio` değer alarak kabul edilip yok sayılıyor. Gerçekten bilinmeyen parametre (ör. `--d`) hata verir. |
| Raporlar `reports/` | `tests/reports/` altına taşındı (`git mv`); `differential.py` varsayılan raporu `tests/reports/differential_report.md`. |

## Geçerli tasarım kararları (SPEC'te tanımlı değil)

> Sözleşme v1.0.0 (SPEC §0) aşağıdaki maddelerden ayrıştırma, hata biçimi, çıkış kodları ve JSON biçimiyle ilgili olanların yerini aldı; geçerli hâlleri "Sözleşme uyumu" bölümünde.

1. **Brent ayrıntıları.** Klasik zeroin (Brent 1973) yapısı; ters kuadratik/sekant adımı kabul ölçütleri ve en küçük
   adım için durma ölçütündeki tol1 = 1.11e-16·|b| kullanılır. tol1 yarım ulp mertebesinde olduğundan `b + adım == b`
   olursa b bir ulp ilerletilir (`math.nextafter`); SPEC en küçük adımı tanımlamıyor. Çağrıda geçirildiği söylenen
   1e-10 kullanılmıyor (§4.5/3: kullanımı gözlenmedi).
2. **Aralık genişletmede taşma** → hata (yukarıda).
3. **Kritik değer** `chi2.isf(α, df)` ile hesaplanır (matematiksel olarak (1 − α) quantile'ı; küçük α'da 1 − α'nın
   yuvarlama kaybını önler). Güç SPEC §4.3'teki gibi `1 − CDF` ile hesaplanır; λ < 1e-100 için merkezi χ² CDF.
   Merkezi olmayan CDF için scipy `ncx2.cdf` kullanılır (§4.4 izin veriyor); G*Power'ın Poisson toplamı yeniden yazılmadı.
4. **Post hoc kesirli N (A-3)** reddedilir: `Total sample size must be an integer.` (uydurma mesaj). Önce aralık
   kontrolü yapılır, sonra tamsayılık (0.5 → aralık mesajı). `1e2` gibi tamsayı değerli yazımlar kabul edilir.
5. **Ayrıştırma hataları** (S-2: SPEC v1.2 bunu tasarım kararı olarak bırakıyor; mesajlar İngilizce): eksik
   `--test`/`--mode`/zorunlu parametre, bilinmeyen parametre/test/mod, sayıya çevrilemeyen ya da sonlu olmayan değer
   (NaN, ±∞). Kontrol sırası: argparse (bilinmeyen parametre) → test → mod → zorunlu parametre varlığı → sayıya
   çevirme → motor doğrulaması (§2.1 sırası). Yani eksik bir parametre, var olan bir df hatasından önce raporlanır.
6. **Çıkış kodları:** başarı 0, girdi/ayrıştırma hatası 1, beklenmeyen iç hata 2. Hata JSON'u stdout'a yazılır.
7. **JSON biçimi:** boşluksuz (`separators=(",", ":")`), alan sırası `n_total, actual_power, critical, df, ncp`;
   `n_total` her zaman tamsayıdır (G-013'te 7848860509327).
8. **Seçenek kısaltmaları** kapalı (`allow_abbrev=False`); `--w=0.3` biçimi kabul edilir.
9. **Diferansiyel düzenek:** hata vektöründe `notes` hücresinde metin içinde çift tırnak varsa tırnak içi, yoksa
   (hücrenin tamamı CSV tırnağıyla yazılmışsa) hücrenin tamamı beklenen mesajdır. KAPI oranı muhafazakâr hesaplanır:
   bilimsel gösterimli `n_total` (A-5) tam eşleşme sayılmaz; doğrulanabilirler üzerindeki oran ayrıca verilir.
   Fixture'daki `df_out` hücreleri SPEC'te yoktur; girdi df'nin G*Power'daki olası görünümü (`1`, `2.5`) yazıldı.

## SPEC'e dair sorular / açık noktalar

- **A-1** Kapandı: alan adları sözleşmede tanımlı (§0.1). Eş adlar kaldırıldı (bkz. "Sözleşme uyumu").
- **A-2** Sayılar tam hassasiyetle yazılıyor (yuvarlamasız double).
- **A-3** Post hoc kesirli N → hata (karar 4). G*Power davranışı bilinmiyor.
- **A-4** Kritik değer yöntemi: scipy `chi2.isf`; SPEC'teki 30 vektörün tüm `critical` değerleri ekran basamağında tuttu.
- **A-5** G-013: bizim n_total = 7848860509327; ekranda `7.8489e+12` → yalnızca 5 anlamlı basamakta doğrulandı.
  Tam değer doğrulanamaz; KAPI'de "doğrulanamayan" olarak raporlanıyor.
- **S-1** Yanıtlandı (§5.1, §4.5/3, §4.5/5) ve uygulandı: kök bulucu 0 / son tahmin döndürür, uydurma hata kalktı.
- **S-2** Yanıtlandı: mesaj metni ve sıra tasarım kararı (karar 5); §2.2 mesajları birebir korunuyor.
- **S-3** v1.2'de uygulanmıştı; sözleşme v1.0.0 ile **kalktı**: df artık çıktı değil.
- **S-4** v1.2'de yok sayma olarak uygulanmıştı; sözleşme v1.0.0 ile **kalktı**: hepsi `UNKNOWN_PARAM`.

## Uyuşmazlıklar

SPEC §6'daki 30 vektörün hiçbirinde uyuşmazlık yok; statsmodels karşılaştırmasında da yok. Sayı ayarı yapılmadı.
