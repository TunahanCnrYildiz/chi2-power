# YZM301 Teardown Sprint · χ² Olumsallık Tablosu (Konu 4)

> **Yapılan katmanlar**
> - ✅ **Temel katman (CLI):** tamamlandı. KAPI geçti: N tam eşleşme %93.33; doğrulanabilir vektörlerde %100.
> - ☐ MCP sunucusu (+15): yapılmadı
> - ☐ AI ajanı (+10): yapılmadı

G\*Power 3.1.9.7'nin **χ² testi, olumsallık tablosu** hesabının temiz oda yöntemiyle yeniden yazımıdır.
`gpower-clone` G\*Power değildir ve G\*Power ekibiyle bir bağı yoktur (bkz. [Atıf](#atıf)).

Çalışma bireyseldir.

## Hızlı başlangıç

Gereksinim: Python ≥ 3.10 (Python 3.14 ile geliştirildi ve test edildi).

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[test,diff]"
```

Linux ve macOS'ta `.venv/Scripts/` yerine `.venv/bin/` kullanılır. Kurulumdan sonra `gpower-clone` komutu sanal ortamda hazırdır.

**A priori: gereken toplam N**

```bash
gpower-clone --test chi2-contingency --mode a-priori --w 0.3 --alpha 0.05 --power 0.95 --df 1
```

```json
{"n_total":145,"actual_power":0.9507851454132252,"critical":3.8414588206941285,"df":1,"ncp":13.049999999999999}
```

**Post hoc: ulaşılan güç**

```bash
gpower-clone --test chi2-contingency --mode post-hoc --w 0.3 --alpha 0.05 --n 100 --df 1
```

**Geçersiz girdi.** Tek satır JSON hata ve sıfırdan farklı çıkış kodu verir:

```bash
gpower-clone --test chi2-contingency --mode a-priori --w 0.3 --alpha 0.05 --power 0.8 --df 0
```

```json
{"error":"Degrees of Freedom must be greater or equal one."}
```

`python -m gpower_clone …` de aynı şekilde çalışır.

### CLI sözleşmesi

| Parametre | Mod | Anlamı | Geçerli aralık |
|---|---|---|---|
| `--test chi2-contingency` | ikisi | test ailesi | — |
| `--mode a-priori` \| `post-hoc` | ikisi | analiz türü | — |
| `--w` | ikisi | etki büyüklüğü w | a priori: w ≥ 1e-6 · post hoc: w ≥ 0 |
| `--alpha` | ikisi | α | [1e-7, 0.9999999] |
| `--power` | a priori | güç (1 − β) | [1e-7, 0.9999999] ve ≥ α |
| `--n` | post hoc | toplam N | tamsayı, [1, 2147483646] |
| `--df` | ikisi | serbestlik derecesi | ≥ 1 (kesirli df geçerli) |

- **Çıktı alanları:** `n_total` (tamsayı), `actual_power`, `critical`, `df`, `ncp`. Sayılar yuvarlanmadan tam hassasiyetle yazılır.
- **Neden n1/n2 yok:** Bu testte grup yoktur, yalnızca toplam N vardır.
- **Eş adlar:** `--n-total` ve `--n_total`, `--mode posthoc` da kabul edilir.
- **Yok sayılan parametreler:** Yönergenin genel parametreleri `--tails` ve `--ratio` kabul edilir ve yok sayılır.
- **Adların kaynağı:** Yönergedeki `[LİNK: CONTRACT.md]` bağlantısı boş olduğu için χ²'ye özgü adlar (`--w`, `--df`, `--n`) yönergedeki örnek çağrının adlandırma mantığından çıkarıldı. Ayrıntılı gerekçe SPEC §2 ve §5.1'de.

### Testler ve raporlar

```bash
.venv/Scripts/python -m pytest -q
.venv/Scripts/python tests/differential.py --csv oracle/vectors.csv --report tests/reports/differential_report.md
.venv/Scripts/python tests/statsmodels_vectors.py
```

- `pytest` şunları çalıştırır: kabul testleri (SPEC §6'nın her vektörü ayrı test), motor ve CLI birim testleri, G\*Power kâhinine karşı KAPI testi ve 894 vektörlük statsmodels regresyonu.
- `differential.py` CLI'yi gerçek bir alt süreç olarak çalıştırır ve sonucu G\*Power'ın ekrandaki basamak sayısıyla karşılaştırır.
- `statsmodels_vectors.py`, statsmodels `GofChisquarePower` ile 894 vektör üretir ve karşılaştırır.

## Sonuçlar

| Ölçüm | Sonuç | Kaynak |
|---|---|---|
| pytest | **94 geçti, 0 atlandı** | `tests/` |
| G\*Power arayüz vektörleri (kâhin) | **30/30** vektör tüm alanlarda tutuyor (23 hesap + 7 hata mesajı) | [`tests/reports/differential_report.md`](tests/reports/differential_report.md) |
| **KAPI** (N tam eşleşme, eşik %90) | **%93.33 → GEÇTİ.** Doğrulanabilir vektörlerde %100. | aynı rapor |
| statsmodels ölçek testi | 894 vektör (594 a priori, 300 post hoc), **uyuşmazlık yok** | [`tests/reports/statsmodels_report.md`](tests/reports/statsmodels_report.md) |

KAPI oranı temkinli hesaplandı. G-013'te (w = 1e-6) G\*Power, N'yi ekranda yalnızca `7.8489e+12` olarak gösteriyor. Bizim değerimiz 7 848 860 509 327 ve bu gösterimle uyumlu; ama tam tamsayı ekrandan doğrulanamadığı için bu vektörü "eşleşmedi" saydık (SPEC §5, A-5).

### Bulgu: kesirli N → tamsayı N

pwr ve statsmodels N'yi kesirli verir, G\*Power ise tamsayıya çevirir. Kılavuz bunu "kesirli N her zaman yukarı yuvarlanır" diye anlatıyor (LEDGER L-030 `[DOK]`). Binary ise **kılavuzda olmayan** bir ara adım içeriyor (L-021 `[REA]`): N önce 10 ondalık basamağa yuvarlanıyor, sonra yukarı yuvarlanıyor. Bu yüzden kesirli kısmı 5·10⁻¹¹'den küçük bir N aşağı iner; örneğin 104.00000000003 → 104. 594 a priori statsmodels vektörünün hepsinde `n_total = ⌈N_statsmodels⌉`. Hiçbir kök bir tamsayıya bu kadar yakın olmadığından bu ızgarada iki kural ayrışmadı.

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

## Hedef binary

| Alan | Değer |
|---|---|
| Ürün | G\*Power 3.1.9.7 (Windows) |
| Kaynak | Resmi sayfa: https://www.psychologie.hhu.de/arbeitsgruppen/allgemeine-psychologie-und-arbeitspsychologie/gpower |
| Dağıtım dosyası | `GPowerWin_3.1.9.7.zip` — SHA-256 `3BB7F1F2478D74EE5BA701AE7F849373CF2B8A11F6B6216C7C6B236DB7861199` |
| İncelenen çalıştırılabilir | `GPowerNT.exe` (FileVersion 3.1.9.7) |
| `GPowerNT.exe` SHA-256 | `C63E6A133EB6372932F810C08CC33DC35A06D1DDB658F897BD6C34A754EFC812` |

> Not: Ödev metni dosyayı "GPower.exe" diye anıyor; 3.1.9.7 Windows dağıtımında çalıştırılabilir dosyanın adı `GPowerNT.exe`.
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
| `src/gpower_clone/` | `engine.py` (hesabın tek yeri) ve `cli.py` (ince katman) |
| `tests/` | Kabul, birim ve CLI testleri; diferansiyel test; statsmodels karşılaştırması; `tests/reports/` uyum raporları |
| `NOTES.md` | Yazım oturumunun tasarım kararları ve SPEC'e soruları |

## Demo

_TODO: 60 saniyelik CLI videosu bağlantısı_

## Atıf

G\*Power, Franz Faul, Edgar Erdfelder, Albert-Georg Lang ve Axel Buchner tarafından geliştirilmiştir:

- Faul, F., Erdfelder, E., Lang, A.-G., & Buchner, A. (2007). G\*Power 3: A flexible statistical power analysis program for the social, behavioral, and biomedical sciences. *Behavior Research Methods, 39*, 175–191.
- Faul, F., Erdfelder, E., Buchner, A., & Lang, A.-G. (2009). Statistical power analyses using G\*Power 3.1: Tests for correlation and regression analyses. *Behavior Research Methods, 41*, 1149–1160.

Bu çalışma YZM301 dersi kapsamında, eğitim amacıyla yapılmıştır. G\*Power yalnızca resmi sayfasından dağıtılır; bu repo G\*Power'ın hiçbir dosyasını içermez.
