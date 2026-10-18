# NOTES — gpower-clone (χ² olumsallık tablosu, temiz oda yazımı)

Tek davranış kaynağı: `SPEC.md` (şu an v1.2). Başka kaynak açılmadı; tersine mühendislik aracı kullanılmadı.

## Kurulum ve çalıştırma

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[test,diff,mcp]"     # Linux/macOS: .venv/bin/python
```

```bash
gpower-clone --test chi2-contingency --mode a-priori --w 0.3 --alpha 0.05 --power 0.95 --df 1
# {"n_total":145,"actual_power":0.9507851454132252,"critical":3.8414588206941285,"df":1,"ncp":13.049999999999999}
python -m gpower_clone --test chi2-contingency --mode post-hoc --w 0.3 --alpha 0.05 --n 100 --df 1
```

Testler ve raporlar:

```bash
.venv/Scripts/python -m pytest -q                                  # kabul + birim + CLI + düzenek testleri
.venv/Scripts/python tests/differential.py # oracle/vectors.csv → tests/reports/differential_report.md
.venv/Scripts/python tests/differential.py --csv tests/fixtures/spec_vectors.csv --report tests/reports/differential_report_spec.md
.venv/Scripts/python tests/statsmodels_vectors.py                   # tests/reports/statsmodels_{report.md,vectors.csv}
```

`differential.py` çıkış kodu: KAPI geçerse 0, geçmezse 1, CSV yoksa 2. `--cmd "gpower-clone"` ile başka bir komut denenebilir.

## Yapı

| Dosya | Görev |
|---|---|
| `src/gpower_clone/engine.py` | Tüm hesap ve alan doğrulaması: §2.1 sırası, §2.2 mesajları, §4.1–4.4 formülleri (scipy), §4.5 aralık kurma, Brent, yuvarlama |
| `src/gpower_clone/service.py` | Ortak katman: mod adı, zorunlu parametre, motor çağrısı, çıktı sözlüğü (alan sırası, df biçimi), `{"error": …}`, JSON metni |
| `src/gpower_clone/cli.py` | İnce katman: argparse → metin → float → `service.compute` → tek satır JSON |
| `src/gpower_clone/mcp_server.py` | MCP sunucusu (stdio): tek araç, `service.compute`'u çağırır; sayı işleyen kodu yok |
| `tests/test_acceptance.py` | SPEC §6 Gherkin; her vektör ayrı test (15 a priori, 8 post hoc, 7 hata + sıra, yuvarlama örnekleri) |
| `tests/test_engine.py`, `tests/test_cli.py` | §4.5 adımları (x dizisi 50.5, 24.75, …), sınırlar, eş adlar, alt süreç (`python -m`, console script) |
| `tests/differential.py` | `oracle/vectors.csv` ↔ CLI (gerçek alt süreç), ekran basamağında karşılaştırma, uyum raporu |
| `tests/fixtures/spec_vectors.csv` | SPEC §6'daki 30 vektörün CSV biçimi (düzeneği kâhin gelmeden sınamak için) |
| `tests/statsmodels_vectors.py` | statsmodels `GofChisquarePower` ile 894 vektör (594 a priori, 300 post hoc) |
| `tests/test_statsmodels.py` | Aynı 894 vektörlük ızgara pytest regresyon testi olarak |
| `tests/test_mcp.py` | MCP ↔ CLI birebir eşitlik (30 vektör), stdio uçtan uca, ince adaptör kontrolü |
| `src/gpower_clone/agent/` | AI ajanı: Sistem 1, MCP ajanı, puanlama, değerlendirme, GUI karşılaştırması |
| `tests/test_agent.py` | Ajan katmanı (sahte çalıştırıcıyla): kilitli komut, akış ayrıştırma, puanlama, yönlendirme |
| `tests/reports/` | Üretilen uyum raporları (SPEC vektörleri, statsmodels) |

## Sonuçlar

- pytest: **186 geçti, 1 atlandı** (`oracle/vectors.csv` henüz yok → `test_oracle_gate` atlanıyor).
- SPEC vektörleri üzerinde diferansiyel rapor (`tests/reports/differential_report_spec.md`): 30/30 vektör tüm alanlarda tutuyor.
  **KAPI: 22/23 = %95.65** (G-013 doğrulanamayan sayıldığında); doğrulanabilirler üzerinde %100. Eşik %90 → GEÇTİ.
  Not: kâhin CSV'si gelince aynı betik onunla tekrar çalıştırılmalı; bu oran SPEC'teki tablodan türetilmiştir.
- statsmodels (`tests/reports/statsmodels_report.md`): 594/594 a priori vektörde `n_total = ⌈N_sm⌉`; 594/594 minimallik
  (güç(n_total) ≥ hedef, güç(n_total − 1) < hedef); 300/300 post hoc güç 7 ondalıkta eşit (en büyük fark 4.4e-16).
  R `pwr` makinede kurulu olmadığı için kullanılmadı.

### Kesirli N ↔ tamsayı N ilişkisi (SPEC §4.5/4)

statsmodels ve gpower-clone aynı sürekli denklemi (güç(w, α, N) = hedef) çözer. statsmodels kökü kesirli döndürür;
gpower-clone kökü 10 ondalığa yuvarlayıp (⌊N·10¹⁰ + 0.5⌋/10¹⁰) yukarı yuvarlar; sonuç aralığın alt ucundan
küçükse alt uca çeker (§4.5/5). Güç N'de
arttığından bu, hedefe ulaşan en küçük tamsayıdır ve ⌈N_sm⌉'e eşittir. Ayrılık yalnızca kök bir tamsayıya çok
yakınsa olabilir: kesir < 5·10⁻¹¹ ise G*Power kuralı aşağı yuvarlar (104.00000000003 → 104), ayrıca iki çözücünün
toleransı farklıdır. Izgarada kesirli kökler arasındaki en büyük fark 2.5·10⁻⁶ (göreli 2.5·10⁻⁷); kökteki artık
gpower-clone'da 5.6·10⁻¹⁶ (v1.2 durma ölçütüyle; önce 1.5·10⁻¹²), statsmodels'te 8.5·10⁻⁸. Yani fark statsmodels çözücüsünün gevşek toleransından geliyor.
Hiçbir kök bir tamsayıya 10⁻⁶'dan yakın değildi, bu yüzden bu ızgarada kural farkı ortaya çıkmadı.

## MCP sunucusu (bonus katman)

Motorun önünde ince bir adaptör. Akış: `mcp_server.chi2_contingency_power` → `service.compute` → `engine`.
CLI de aynı `service.compute` ve `service.to_json` fonksiyonlarını kullanır. Bu yüzden iki yüzün çıktısı aynı
koddan gelir; MCP modülünde scipy, `math` ya da sayı dönüştürme yoktur (`tests/test_mcp.py` bunu kaynak
düzeyinde denetler). Resmi Python SDK `mcp` 2.3.0 (`mcp.server.mcpserver.MCPServer`; 2.x'te FastMCP bu adı aldı), stdio taşıma.

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

### Araç: `chi2_contingency_power`

Açıklama: *Chi-square contingency table power analysis (G\*Power compatible). a-priori: give power, returns
required n_total. post-hoc: give n, returns actual_power. Invalid input returns isError with {"error": message}.*

Girdi şeması:

| Alan | Tip | Zorunlu | Açıklama (şemadaki metin) |
|---|---|---|---|
| `mode` | `"a-priori"` \| `"post-hoc"` | evet | a-priori: solve N; post-hoc: solve power |
| `w` | number | evet | Effect size w; a-priori >= 1e-6, post-hoc >= 0 |
| `alpha` | number | evet | Alpha, 1e-7..0.9999999 |
| `df` | number | evet | Degrees of freedom, >= 1 (fractional allowed) |
| `power` | number \| null | a priori'de | a-priori only: target power, 1e-7..0.9999999, >= alpha |
| `n` | integer \| null | post hoc'ta | post-hoc only: total N, 1..2147483646 |

Çıktı şeması (`outputSchema`, `structuredContent`); alanlar CLI JSON'u ile aynı ve aynı sırada:

| Alan | Tip | Anlamı |
|---|---|---|
| `n_total` | integer | Toplam N (a priori: hesaplanan; post hoc: girdi) |
| `actual_power` | number | n_total'daki güç |
| `critical` | number | Kritik χ² değeri |
| `df` | number | Kullanılan df (tamsayıya eşitse JSON'da `1`, değilse `2.5`) |
| `ncp` | number | λ = w²·n_total |

Sonuç biçimi:
- Başarı: `isError = false`; `structuredContent` = sonuç sözlüğü; tek metin içeriği = CLI'nin bastığı JSON satırı.
- Girdi hatası: `isError = true`; `structuredContent` = `{"error": "<mesaj>"}`; metin = CLI'nin hata satırı.
  §2.2 mesajları birebir aynıdır. Eksik parametre mesajı MCP'de alan adını kullanır
  (`Missing required parameter: power`); CLI'de bayrak adını (`--power`). Mesaj metni S-2 gereği tasarım kararıdır.
- Şemaya uymayan girdi (ör. `n = 100.5`, `mode = "sensitivity"`, sayı yerine metin) motora ulaşmaz. SDK argüman
  doğrulaması bunu `isError = true` ile reddeder, mesaj pydantic'in mesajıdır ve `structuredContent` yoktur
  (tasarım kararı). CLI'de aynı durumlar `{"error": …}` döndürür. `posthoc` eş adı MCP şemasında yok; enum yalnızca iki değer içerir.

### Test sonuçları (`tests/test_mcp.py`, 34 test)

- (a) Süreç içi: `spec_vectors.csv`'deki 30 vektörün tamamında (7 hata vektörü dahil) MCP sonucu, CLI alt süreç
  çıktısıyla ayrıştırılmış JSON üzerinde birebir eşit. Hem `structuredContent` hem metin içeriği karşılaştırılıyor;
  `isError` CLI çıkış koduna karşılık geliyor. Eksik parametre de ayrıca test ediliyor.
- (b) Uçtan uca: sunucu `python -m gpower_clone.mcp_server` olarak stdio üzerinden gerçek `mcp.Client` ile
  başlatılıyor. Araç listesi, girdi/çıktı şeması ve 6 vektör (2 a priori, 2 post hoc, 2 hata) CLI ile karşılaştırılıyor.
- (c) İnce adaptör: `mcp_server.py` kaynağında scipy, `chi2.`, `ncx2`, `math`, `float(` ve motor fonksiyonları
  geçmiyor; modül `service`'i içe aktarıyor. CLI de motoru doğrudan içe aktarmıyor.

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

- **A-1** `--w`, `--df`, `--n` adları CONTRACT.md ile doğrulanmadı; eş adlar (`--n-total`, `--n_total`, `--mode posthoc`) kabul ediliyor.
- **A-2** Sayılar tam hassasiyetle yazılıyor (yuvarlamasız double).
- **A-3** Post hoc kesirli N → hata (karar 4). G*Power davranışı bilinmiyor.
- **A-4** Kritik değer yöntemi: scipy `chi2.isf`; SPEC'teki 30 vektörün tüm `critical` değerleri ekran basamağında tuttu.
- **A-5** G-013: bizim n_total = 7848860509327; ekranda `7.8489e+12` → yalnızca 5 anlamlı basamakta doğrulandı.
  Tam değer doğrulanamaz; KAPI'de "doğrulanamayan" olarak raporlanıyor.
- **S-1** Yanıtlandı (§5.1, §4.5/3, §4.5/5) ve uygulandı: kök bulucu 0 / son tahmin döndürür, uydurma hata kalktı.
- **S-2** Yanıtlandı: mesaj metni ve sıra tasarım kararı (karar 5); §2.2 mesajları birebir korunuyor.
- **S-3** Yanıtlandı ve uygulandı: tamsayı değerli df → `1`, kesirli → `2.5`.
- **S-4** Yanıtlandı ve uygulandı: `--tails`, `--ratio` ve moda ait olmayan bilinen parametreler yok sayılır.

## Uyuşmazlıklar

SPEC §6'daki 30 vektörün hiçbirinde uyuşmazlık yok; statsmodels karşılaştırmasında da yok. Sayı ayarı yapılmadı.
