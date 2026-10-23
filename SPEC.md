# SPEC · χ² olumsallık tablosu güç analizi

> Bu belge Oturum 2'nin (yazım) göreceği **tek davranış kaynağıdır**.
> Decompile çıktısı, adres ya da kod alıntısı içermez; yalnızca gözlenebilir davranış, algoritmanın özü ve kabul kriterleri.
> Her kuralın sonunda dayandığı kanıt kaydı belirtilir: `(L-0xx)`. Kayıtlar inceleme oturumunun kanıt defterindedir; Oturum 2'nin onları görmesi gerekmez.

- Sürüm: 2.0 · 2026-10-23 (v2.0: eğitmenin arayüz sözleşmesi v1.0.0 → §0, öncelikli; v1.2: §4.5 kök bulucu, §5.1 sorular)
- Referans davranış: G\*Power 3.1.9.7 (Windows), "χ² tests → Goodness-of-fit tests: Contingency tables"
- Beklenen değerlerin kaynağı (kâhin): `oracle/vectors.csv` (G\*Power arayüzü, ekran görüntülü). Bu belgedeki sayılar oradan alınmıştır; hiçbiri ajan tarafından üretilmemiştir.

---

## 0. Arayüz sözleşmesi v1.0.0 (ÖNCELİKLİ)

> Eğitmen, yönergede boş kalan sözleşmeyi 2026-10-21'de yayımladı (sözleşme sürümü **1.0.0**). Bu bölüm **arayüzü** tanımlar ve aşağıdaki §2, §3, §5.1 ve §6 ile çeliştiği her yerde **bu bölüm geçerlidir**. Hesap davranışı (§4) değişmez.
> Sözleşmenin χ² için verdiği açık referans vektörleri (a priori ve post hoc) mevcut hesapla zaten tutuyor (N = 220, güç 0.9502155; post hoc güç 0.6235846).
> Açık referans vektörlerinin 25'i `tests/fixtures/public_vectors.jsonl` dosyasında: 5 aile × 5 mod; χ² dışındaki aileler kapsam dışıdır.

### 0.1 Komut ve alanlar

```
gpower-clone --test chi2-contingency --mode <MODE> --<alan> <değer> ...
```

| Mod | Girdi alanları (birebir bu adlar) | Çıktı alanları (zorunlu) |
|---|---|---|
| `a-priori` | `w`, `alpha`, `power`, `df` | `ncp`, `critical_chi2`, `n_total`, `actual_power` |
| `post-hoc` | `w`, `alpha`, `n_total`, `df` | `ncp`, `critical_chi2`, `power` |
| `compromise` (bonus) | `w`, `beta_alpha_ratio`, `n_total`, `df` | `ncp`, `critical_chi2`, `alpha`, `beta`, `power` |
| `criterion` (bonus) | `w`, `power`, `n_total`, `df` | `ncp`, `critical_chi2`, `alpha` |
| `sensitivity` (bonus) | `alpha`, `power`, `n_total`, `df` | `ncp`, `critical_chi2`, `w` |

- Parametre biçimi `--<alan> <değer>`. Alan adları tablodakiyle **birebir** aynıdır.
- **Varsayılan değer yoktur.** Modun gerektirdiği her alan verilmelidir.
- Tanınmayan alan ya da **modla ilgisiz** bir alan (ör. `post-hoc` modunda `--power`, χ²'de `--tails`) **hatadır**. Önceki "yok say" kararları (S-4) ve eş adlar (`--n`, `--n-total`, `--mode posthoc`) kaldırılır.
- **Tek uzantı:** Ajan katmanının tablo boyutunu (`rows`, `cols`) iletebilmesi için `rows` + `cols`, `df` yerine kabul edilmeye devam eder. Bu, sözleşmede olmayan, belgelenmiş bir uzantıdır. Düzenek bunu kullanmaz.
- Ondalık ayırıcı her zaman noktadır ve işletim sisteminin dil ayarından etkilenmez.
- Her çağrı **2 saniye** içinde tamamlanmalı ve deterministik olmalıdır.

### 0.2 Başarılı çıktı

- `stdout`'a tek satır JSON; log, uyarı vb. yalnızca `stderr`'e. Çıkış kodu `0`.
- Sayılar tam double hassasiyetle yazılır. Tam sayı alanları (`n_total`) JSON tam sayısıdır.
- Çıktı yalnızca §0.1'deki alanları içerir. Fazladan alana izin var ama yazılmaz; özellikle `df` χ²'de **çıktı değildir**.

### 0.3 Sürüm sorgusu

`gpower-clone --version` → tek satır JSON, çıkış kodu 0:
`{"contract_version": "1.0.0", "name": "chi2-power", "engine": "Python <sürüm>, scipy <sürüm>"}`

### 0.4 Hata çıktısı

- `stdout`'a tek satır JSON: `{"error": "<açıklama>", "code": "<KOD>", "field": "<alan ya da null>"}`.
- **Çıkış kodları:** `2` geçersiz girdi; `1` iç hata (hesap yapılamadı, beklenmeyen durum).
- `error` metni mümkünse G\*Power'ın mesajıdır (§2.2); kod ve alan aşağıdaki tabloya göre seçilir.

| Durum | `code` | `field` |
|---|---|---|
| Modun gerektirdiği alan yok | `MISSING_PARAM` | eksik alan |
| Tanınmayan alan ya da modla ilgisiz alan | `UNKNOWN_PARAM` | o alan |
| Sayı değil; tam sayı olması gereken yerde ondalık (`n_total`, `df`); NaN/±∞ | `INVALID_VALUE` | o alan |
| Sözleşme aralığı dışında (§0.5) ya da G\*Power'ın reddettiği değer (§2.2: α, güç, w ≥ 1e-6, df ≥ 1, N üst sınırı) | `OUT_OF_RANGE` | o alan |
| güç < α (`Power must be greater than or equal to alpha.`) | `INCONSISTENT` | `power` |
| Bilinmeyen `--test` ya da `--mode`; χ² dışındaki aileler | `UNSUPPORTED` | `test` ya da `mode` |
| Girdiler geçerli ama sonuç üretilemiyor (ör. aralık genişletmede taşma) | `NO_SOLUTION` | null |

Doğrulama sırası: önce ayrıştırma (`test` → `mode` → tanınmayan/ilgisiz alan → eksik alan → tür), sonra alan kuralları (§2.1 sırası).

### 0.5 Sözleşme aralıkları (G\*Power'dan sıkı olanlar)

Sözleşme der ki: "Bu aralıkların dışındaki bir değer `OUT_OF_RANGE` ile reddedilir; aralığın içindeki bir değerin kabulüne G\*Power'ın davranışı karar verir."

| Alan | Tür | Sözleşme aralığı | G\*Power'dan farkı |
|---|---|---|---|
| `alpha`, `power` | ondalık | 0 < x < 1 | İçerideki ama G\*Power'ın reddettiği değerler (ör. 1e-8, 0.99999999) yine `OUT_OF_RANGE` (§2.2) |
| `w` | ondalık | **w > 0** | G\*Power post hoc'ta w = 0'ı kabul eder (G-023); sözleşme gereği **reddedilir** |
| `n_total` | tam sayı | **≥ 2** | G\*Power N = 1'i kabul eder (G-025); sözleşme gereği **reddedilir** |
| `df` | tam sayı | **≥ 1** | G\*Power kesirli df'yi kabul eder (G-019); sözleşme gereği df = 2.5 `INVALID_VALUE` ile **reddedilir** |
| `beta_alpha_ratio` | ondalık | > 0 | — |

Bu üç fark bilinçli bir **sözleşme kararıdır**. Diferansiyel raporda bu vektörler "sözleşme gereği G\*Power'dan farklı" diye ayrı gösterilir; uyuşmazlık sayılmaz.

### 0.6 Karşılaştırma toleransı

- Tam sayılar tam eşleşmelidir.
- Ondalıklar için |fark| ≤ 1e-6 ya da göreli fark ≤ 1e-6 yeterlidir.
- Diferansiyel test bu kurala göre güncellenir; ekran basamağı kuralı da bu toleransın içinde kalır.

### 0.7 Bonus modlar (compromise, criterion, sensitivity)

Bu modlar binary'de incelenmedi; davranışları **yayımlanmış yöntemden** tanımlanır ve sözleşmenin açık referans vektörleriyle (`tests/fixtures/public_vectors.jsonl` içindeki `chi2-contingency/*`) doğrulanır. Bütün modlarda λ = w² · n_total ve merkezi olmayan χ² CDF'i §4.3 – §4.4'teki gibidir.

- **sensitivity:** α, güç, n_total, df verilir. Merkezi olmayan χ²'nin gücü 1 − F(c; df, λ) = güç olacak şekilde λ ≥ 0 bulunur; c = merkezi χ²(df)'nin 1 − α quantile'ıdır. Sonra w = √(λ / n_total). Çıktı: `ncp` = λ, `critical_chi2` = c, `w`.
- **criterion:** w, güç, n_total, df verilir. λ = w²·n_total. 1 − F(c; df, λ) = güç olacak şekilde c bulunur, sonra α = 1 − F₀(c; df). Çıktı: `ncp`, `critical_chi2` = c, `alpha`.
- **compromise:** w, q = `beta_alpha_ratio`, n_total, df verilir. λ = w²·n_total. α(c) = 1 − F₀(c; df) ve β(c) = F(c; df, λ) olmak üzere β(c) / α(c) = q olacak şekilde c bulunur. Çıktı: `ncp`, `critical_chi2` = c, `alpha`, `beta`, `power` = 1 − β.
- **Kök bulma:** Herhangi bir hassas kök bulucu kullanılabilir (çözüm 1e-6 toleransın çok altında olmalı).
- **Etiket:** Bu kuralların G\*Power içindeki gerçekleştirimi incelenmediği için kanıt defterinde `[AJAN]` olarak etiketlenir; doğrulamaları referans vektörleridir.
- **Kabul kriterleri:** Sözleşmenin üç χ² vektörü, 1e-6 toleransla:
  - compromise: c = 7.6804954, α = β = 0.1747455, güç = 0.8252545
  - criterion: c = 4.6618452, α = 0.4585253
  - sensitivity: λ = 19.7801344, c = 11.0704977, w = 0.4447486

### 0.8 MCP ve ajan

- **MCP:** Tek araç **`power_analysis`**. Girdi şeması CLI ile **aynı alan adlarını** kullanır; `test` ve `mode` zorunludur. Çıktı, CLI'nin stdout JSON'u ile **aynıdır** ve metin içeriği olarak döner; hatada aynı hata JSON'u döner. Eşdeğerlik testi: 25 açık referans vektörünün her biri için CLI ve MCP çıktısı aynı olmalı (χ² dışındaki ailelerde ikisi de aynı `UNSUPPORTED` hatasını döndürür).
- **Ajan kayıtları:** Her araç çağrısı `logs/agent_calls.jsonl` dosyasına bir satır olarak yazılır: `{"ts": "<ISO-8601>", "question": "...", "tool_input": {...}, "tool_output": {...}, "tokens_in": <int>, "tokens_out": <int>}`. Yalnızca kurgusal senaryolar kullanılır.
- **"Orta etki" bir kategoridir.** Ajan, "orta etki" gibi bir kategoriden değer çıkardığında (w = 0,3) bu varsayımı kullanıcıya açıkça söylemelidir.

---

## 1. Kapsam

| Konu | Karar |
|---|---|
| Test | χ² testi, olumsallık tablosu; CLI etiketi `chi2-contingency` |
| Modlar | `a-priori` (toplam N hesapla), `post-hoc` (güç hesapla) |
| Kapsam dışı | Sensitivity, criterion, compromise modları (G\*Power'da var, ödev kapsamında değil) (L-012) |
| Grup oranı | **Uygulanamaz.** Bu test tek bir toplam örneklem büyüklüğü (N) kullanır; n1/n2 ya da grup oranı parametresi yoktur. Yönergedeki "eşit olmayan grup oranı" sınır değeri bu aile için tanımsızdır. (L-012) |

## 2. Girdiler

> **CLI sözleşmesinin kaynağı.** Classroom duyurusu "CLI sözleşmesi ekteki dosyada" diyor. Yönerge dosyasında yalnızca t testi örneği var: `gpower-clone --test t2-indep --mode a-priori --tails 2 --d 0.5 --alpha 0.05 --power 0.95 --ratio 1`. Diğer aileler için verilen `[LİNK: CONTRACT.md]` bağlantısı ise boş.
> - **Kesin olanlar:** Komut adı `gpower-clone`. `--test chi2-contingency` (aynı etiket yönergedeki etiket listesinde de geçiyor). `--mode a-priori`, `--alpha`, `--power`. Tek satır JSON çıktı ve hata biçimi.
> - **Örnekten çıkarılanlar:** `--w`, `--df`, `--n`, `--mode post-hoc`. Örnek çağrı, etki büyüklüğünü G\*Power'daki sembolüyle adlandırıyor (`--d`); aynı mantıkla `--w` ve G\*Power alanı "Df" için `--df`.
> - **Esneklik:** Gizli vektörlerin farklı bir yazım kullanma riskine karşı CLI şu eş adları da kabul eder: N için `--n-total` ve `--n_total`, post hoc için `--mode posthoc`. Sözleşmenin genel parametreleri `--tails` ve `--ratio` ile moda ait olmayan bilinen parametreler kabul edilir ve yok sayılır (§5.1, S-4).

| Kavram | CLI adı | Tip | Mod | Geçerli aralık | Kaynak |
|---|---|---|---|---|---|
| Test | `--test` | metin | her ikisi | `chi2-contingency` | yönerge |
| Mod | `--mode` | metin | her ikisi | `a-priori` \| `post-hoc` | yönerge |
| Etki büyüklüğü w | `--w` | ondalık | a priori | w ≥ 1e-6 | L-016 |
| Etki büyüklüğü w | `--w` | ondalık | post hoc | w ≥ 0 (w = 0 geçerli) | L-017 |
| α | `--alpha` | ondalık | her ikisi | 1e-7 ≤ α ≤ 0.9999999 | L-013 |
| Güç (1 − β) | `--power` | ondalık | a priori | 1e-7 ≤ güç ≤ 0.9999999 **ve** α ≤ güç (güç = α geçerli) | L-014, L-007 |
| Toplam N | `--n` | tamsayı | post hoc | 1 ≤ N ≤ 2 147 483 646 | L-015 |
| Serbestlik derecesi df | `--df` | ondalık | her ikisi | df ≥ 1 (kesirli df reddedilmez) | L-006 |

### 2.1 Doğrulama sırası

İlk başarısız kontrol hatayı belirler; sonraki kontroller yapılmaz. (L-012)

- **a priori:** df → w → α → güç → α ≤ güç
- **post hoc:** df → w → α → N

### 2.2 Geçersiz girdi davranışı

- Çıktı tek satır JSON olmalı: `{"error":"<açıklama>"}`. Çıkış kodu sıfırdan farklı olmalı. (yönerge)
- Açıklama, G\*Power'ın mesajıyla **birebir aynı** olmalıdır. Mesajlar binary'den (L-006, L-007, L-013 – L-017) ve arayüzden doğrulanmıştır:

| Durum | Mesaj (birebir) | Oracle |
|---|---|---|
| df < 1 | `Degrees of Freedom must be greater or equal one.` | G-008 |
| güç < α | `Power must be greater than or equal to alpha.` | G-015 |
| α aralık dışı | `Alpha is outside the admissible range (1e-07, 1).` | G-016 |
| güç aralık dışı | `Power is outside the admissible range (1e-07, 1).` | G-018 |
| N aralık dışı | `Total sample size is outside the admissible range (1, 2147483646)` (sonunda nokta yok) | G-026 |
| a priori, w < 1e-6 | `Effect size w must be greater 1e-06.` | G-014 |
| post hoc, w < 0 | `Effect size w must be non-negative.` | G-024 |

> Not: Aralık mesajlarında üst sınır 0.9999999, G\*Power'ın 6 anlamlı basamaklı yazdırması nedeniyle `1` olarak görünür. Kabul edilen aralık yine de [1e-7, 0.9999999]'dur: 0.9999999 kabul edilir (G-017), 0.99999999 reddedilir (G-018).

- Sayıya çevrilemeyen değer, eksik ya da bilinmeyen parametre, bilinmeyen test ya da mod da aynı biçimde hata verir.
- Sayı olmayan değerler (NaN, ±∞) de geçersizdir. G\*Power'da bu durum gözlenmedi; bu bir tasarım kararıdır.

## 3. Çıktılar

Çıktı **tek satır JSON**'dur. Alan adları yönergedeki örnek çıktıyla uyumludur. Kesin liste `CONTRACT.md` ile doğrulanacak.

| Alan | a priori | post hoc | Anlamı | Kaynak |
|---|---|---|---|---|
| `n_total` | ✔ (tamsayı) | ✔ (girdi N) | Toplam örneklem büyüklüğü | L-018, L-021 |
| `actual_power` | ✔ | ✔ | a priori: yuvarlanmış N ile gerçek güç; post hoc: hesaplanan güç | L-022, L-023 |
| `critical` | ✔ | ✔ | Kritik χ² değeri | L-023 |
| `df` | ✔ | ✔ | Kullanılan serbestlik derecesi | L-012 |
| `ncp` | ✔ | ✔ | Merkezi olmama parametresi λ | L-023 |

- `n1`, `n2` alanları bu testte yoktur (§1, grup oranı).
- **Tolerans** (yönerge): `n_total` **tam** eşleşmeli. Diğer alanlar G\*Power'ın ekranda gösterdiği basamağa kadar eşleşmeli.
  - Ekranda değerler çoğunlukla 7 ondalık basamakla gösterilir (ör. `0.9507851`, `3.8414588`, `13.0500000`).
  - Ancak basamak sayısı her zaman 7 değildir:
    - Tamsayı değerli λ ondalıksız gösterilir: `0` (G-023), `1000` (G-027).
    - Büyük bir kritik değer 4 ondalıkla gösterilir: `149.4493` (G-021).
    - Çok büyük N bilimsel gösterimle gösterilir: `7.8489e+12` (G-013).
  - Bu yüzden karşılaştırma **vektör başına, ekranda görünen basamak sayısıyla** yapılır. `oracle/vectors.csv` değerleri ekrandaki metin olarak saklar.
  - Uygulama değerleri en az 7 ondalık basamak doğrulukla üretmelidir.
- Çok büyük N: A priori N için üst sınır kontrolü yoktur. N, 2 147 483 646'yı aşabilir (G-013: w = 1e-6 → N ≈ 7.8489·10¹²). `n_total` bu durumda da bir tamsayıdır. (L-012, L-018)

## 4. Hesap kuralları

### 4.1 Merkezi olmama parametresi
λ = w² · N. Post hoc'ta N girdi N'dir. A priori'de N, aramada kesirli değerdir; çıktıdaki λ ise yuvarlanmış N ile hesaplanır. (L-023, L-027, oracle G-001 – G-007)

### 4.2 Kritik değer
`critical` = merkezi χ²(df) dağılımının (1 − α) quantile'ıdır. w'ye ve N'ye bağlı değildir. (L-023)

### 4.3 Güç (post hoc ve a priori'deki "gerçek güç")
güç = 1 − F(critical; df, λ). Burada F, merkezi olmayan χ² dağılımının CDF'idir. (L-023)

### 4.4 Merkezi olmayan χ² CDF'i
- λ < 1e-100 ise merkezi χ² CDF'i kullanılır. (L-008)
- Aksi hâlde CDF, Poisson(λ/2) ağırlıklı merkezi χ²(df + 2k) CDF'lerinin toplamıdır. G\*Power bu toplamı en büyük ağırlıklı terimden (k = ⌊λ/2⌋) başlatır, iki yöne ilerler ve eklenen terim, toplamın makine epsilonu (≈ 2.22e-16) katının altına düşünce durur. (L-024)
- Özel durumlar: x ≤ 0 → 0; x = +∞ → 1. (L-024)
- Uygulama, merkezi ve merkezi olmayan dağılım fonksiyonları için hazır bir kütüphane (ör. scipy) kullanabilir; yönerge buna izin veriyor. Sonuçlar §3'teki toleransı sağlamalıdır. Dağılım kendi yazılırsa kütüphane yalnızca testlerde kullanılır (yönerge).

### 4.5 A priori: toplam N araması
N, aşağıdaki adımlarla bulunur. Puanlamada belirleyici olan adımlar 2–5'tir.

1. **Hedef fonksiyon:** f(N) = güç(w, α, N) − hedef güç. Burada güç §4.3'teki formüldür ve N **kesirli** bir sayı olarak kullanılır. (L-027)
2. **Arama aralığı** (alt sınır a = 1, başlangıç 100) (L-019, L-028):
   - **f(100) < 0:** alt = 100, üst = 160. f(üst) < 0 olduğu sürece alt ← üst, üst ← üst × 1.6.
   - **f(100) ≥ 0:** üst = 100, x = (a + 100) × 0.5. x ≥ a ve f(x) > 0 olduğu sürece üst ← x, x ← (x + a) × 0.5 − a. Döngü bitince alt ← x.
     Not: Bu adım standart yarılama değildir. a = 1 için x dizisi 50.5, 24.75, 11.875, 5.4375, 2.21875, 0.609… şeklindedir.
   - Son olarak alt < 1 ise alt ← 1.
3. **Kök bulma:** [alt, üst] aralığında Brent tarzı bir kök bulucu (ikiye bölme + ters kuadratik/sekant adımları) kullanılır. En fazla 300 iterasyon yapılır. (L-018, L-020)
   - **Durma ölçütü:** |yarım aralık| ≤ 1.1102230246251565·10⁻¹⁶ · |b| (b: o anki en iyi tahmin) ya da f(b) = 0. Çağrıda ayrıca 1e-10 değeri geçirilir; ancak döngüdeki durma koşulunda bu değerin kullanıldığı gözlenmedi. Pratikte iki ölçüt de sonucu değiştirmez: kök, 4. adımdaki 10 basamaklı yuvarlamadan çok daha hassas bulunur. (L-018, L-020)
   - **Uçlarda f aynı işaretli:** Kök bulucu hata vermez; **0** döndürür. (L-020)
   - **300 iterasyon dolarsa:** Kök bulucu hata vermez; **son tahmini (b)** döndürür. (L-020)
   - G\*Power'ın a priori yolunda kök bulucudan kaynaklanan bir hata mesajı yoktur. Sonuç her zaman 4. ve 5. adımlardan geçer.
4. **Yuvarlama:** Bulunan kesirli N önce 10 ondalık basamağa yuvarlanır: N′ = ⌊N · 10¹⁰ + 0.5⌋ / 10¹⁰. Sonra yukarı yuvarlanır: n_total = ⌈N′⌉. Bu nedenle kesirli kısmı 5·10⁻¹¹'den küçük olan bir N aşağı iner (ör. 104.00000000003 → 104), daha büyük her kesir yukarı çıkar. (L-021)
5. **Alt sınır:** n_total, 2. adımda bulunan **alt** değerinden küçükse n_total = alt olur ve 4. adımdaki yuvarlamadan bir kez daha geçirilir. (L-018)
   - alt her zaman ≥ 1'dir (2. adımın son kuralı).
   - Uçlarda f'nin aynı işaretli olabildiği tek durum, daraltma döngüsünün x < 1'e inip alt = 1 olmasıdır. Bu durumda kök bulucu 0 döndürür, 4. adım 0 verir ve 5. adım n_total = 1 yapar. Örnek: güç = α (G-007). (L-018, L-020, L-028)
6. **Çıktılar:** actual_power, ncp ve critical, **yuvarlanmış** n_total ile hesaplanır (§4.1 – §4.3). (L-022)

> **Neden önemli?** pwr (R) ve statsmodels (Python) N'yi kesirli verir; G\*Power ise 4. adımdaki kuralla tamsayıya çevirir. İki kaynak arasındaki farklar diferansiyel test raporunda bu kurala bağlanarak açıklanmalıdır. (yönerge, kâhin notu)

### 4.6 Sayısal sınırlar
- Güç = α geçerli bir girdidir. Bu durumda çok küçük bir N bulunur ve alt sınır kuralı (§4.5/5) devreye girebilir. Örneğin G-007'de n_total = 1 ve gerçek güç hedefin üstündedir. (L-007, L-018)
- df ondalık olarak karşılaştırılır ve **kesirli df kabul edilip hesapta aynen kullanılır.** Örneğin df = 2.5 için kritik değer 6.9280761 ve N = 115'tir (G-019). (L-006)
- Post hoc'ta w = 0 geçerlidir: λ = 0 olur ve güç = α çıkar (G-023). (L-017)
- Çok büyük güç ve N değerlerinde güç ekranda `1.0000000` olarak görünür (G-027).

## 5. Bilinen açık noktalar

Bu konularda Oturum 2 varsayım yapmamalıdır. Bir uyuşmazlık çıkarsa test raporunda açıklanmalıdır.

| # | Konu | Durum |
|---|---|---|
| A-1 | χ² ailesine özgü parametre adları (`--w`, `--df`, `--n`) | Yönergedeki `[LİNK: CONTRACT.md]` bağlantısı boş; ekli öğrenci/grup listesinde de sözleşme yok. Adlar §2'deki gibi örnek çağrıdan çıkarıldı, eş adlar da kabul ediliyor. Hocaya Classroom yorumuyla sorulacak. |
| A-2 | JSON'daki ondalık basamak sayısı. Yönerge örneği 4 basamak, G\*Power ekranı çoğunlukla 7 basamak gösteriyor. | Tam hassasiyet (yuvarlamasız double) üretilir. Değer, hangi basamağa yuvarlanarak karşılaştırılırsa karşılaştırılsın doğru sonucu verir; erken yuvarlama ise 7 basamaklı karşılaştırmayı bozar. |
| A-3 | Post hoc'ta N'ye kesirli değer girildiğinde G\*Power'ın davranışı | Gözlenmedi. CLI kesirli N'yi hata olarak reddeder (tasarım kararı). |
| A-4 | Merkezi χ² quantile'ının G\*Power içindeki iç yöntemi | İncelenmedi. §3 toleransı kütüphane quantile'ıyla doğrulanır (30 vektörde kontrol edilecek). |
| A-5 | G-013'te (N ≈ 7.8489·10¹²) N'nin tam tamsayı değeri | Ekran yalnızca 5 anlamlı basamak gösteriyor. Bu vektörde `n_total` ekrandaki gösterim hassasiyetinde karşılaştırılır. KAPI hesabında "tam eşleşmesi doğrulanamayan vektör" olarak raporlanır. |

### 5.1 Yazım oturumunun soruları ve yanıtları (SPEC v1.2)

| # | Soru | Yanıt | Dayanak |
|---|---|---|---|
| S-1 | G-007'de (güç = α) kök bulucu "kök bulunamaz" durumundayken G\*Power ne döndürüyor? | Hata yok. Kök bulucu 0 döndürür, yuvarlama 0 verir, alt sınır kuralı N'yi alt = 1 yapar. Ayrıca 300 iterasyon dolduğunda da hata verilmez, son tahmin kullanılır. Bu nedenle a priori yolda kök bulucudan kaynaklanan **uydurma bir hata mesajı olmamalıdır**. Yalnızca aralık genişletmenin taşması (üst → ∞) gibi G\*Power'da gözlenmemiş durumlar için tasarım kararı serbesttir. | §4.5/3, §4.5/5 (L-018, L-020, L-028); oracle G-007, G-025 |
| S-2 | Ayrıştırma ve eksik parametre hatalarının mesaj metni ve öncelik sırası nedir? | G\*Power'da bir karşılığı yoktur; arayüzde eksik ya da bilinmeyen parametre olamaz. Yönerge yalnızca `{"error":"<açıklama>"}` ve sıfırdan farklı çıkış kodu ister. Mesaj metni ve sıra tasarım kararıdır. SPEC §2.2'deki G\*Power mesajları ise birebir korunmalıdır. | yönerge (CLI sözleşmesi); kanıt yok |
| S-3 | Çıktıdaki `df` tamsayı mı (`1`) ondalık mı (`1.0`) yazılmalı? | df içeride ondalık sayıdır ve kesirli olabilir. Ancak yönergedeki örnek çıktı tamsayı değerli df'yi tamsayı biçiminde yazar (`"df":208`). Karar: df bir tamsayıya eşitse tamsayı biçiminde (`1`), değilse ondalık biçimde (`2.5`) yazılır. | L-006, oracle G-019; yönerge örnek çıktısı |
| S-4 | Moda ait olmayan parametreler (ör. a priori'de `--n`) hata mı olmalı? | G\*Power'da karşılığı yoktur; arayüz yalnızca seçili modun alanlarını gösterir. Gizli vektörler bütün takımlarda "aynı düzenekle" çalıştırılacağı için düzenek, yönergenin genel sözleşmesindeki `--tails` ve `--ratio` parametrelerini her teste geçirebilir. Karar: moda ait olmayan bilinen parametreler ve sözleşmenin genel parametreleri (`--tails`, `--ratio`) **kabul edilir ve yok sayılır**. Gerçekten bilinmeyen bir parametre ise hata verir. | yönerge (örnek çağrı); kanıt yok |

## 6. Kabul kriterleri

> Değerler `oracle/vectors.csv` dosyasından alınmıştır (G\*Power 3.1.9.7 arayüzü; ekran görüntüleri `oracle/screenshots/`).
> `n_total` tam eşleşmeli. Diğer sayısal alanlar, ekranda gösterilen basamak sayısında eşleşmelidir (§3).

```gherkin
# §0 ile uyum: alan adları critical_chi2 / power; çıktıda df yok; G-019 (df 2.5), G-023 (w 0), G-025 (N 1)
# sözleşme gereği hata verir (§0.5) — aşağıdaki tablolarda G*Power davranışı bilgi için durur.
Feature: χ² olumsallık tablosu güç analizi (G*Power 3.1.9.7 ile uyumlu)

  Background:
    Given test ailesi "chi2-contingency"

  # ---------- A priori ----------

  Scenario Outline: A priori modda gereken toplam N
    Given mod "a-priori"
    And w <w>, alpha <alpha>, power <power>, df <df>
    When hesaplama yapılır
    Then çıkış kodu 0 olur
    And "n_total" tam olarak <n_total> olur
    And "actual_power", 1e-6 toleransla <actual_power> olur
    And "critical_chi2", 1e-6 toleransla <critical> olur
    And "ncp", 1e-6 toleransla <ncp> olur

    Examples: G*Power arayüz vektörleri — tipik değerler
      | id    | w    | alpha | power | df  | n_total | actual_power | critical   | ncp        |
      | G-001 | 0.3  | 0.05  | 0.95  | 1   | 145     | 0.9507851    | 3.8414588  | 13.0500000 |
      | G-002 | 0.3  | 0.05  | 0.80  | 4   | 133     | 0.8013043    | 9.4877290  | 11.9700000 |
      | G-003 | 0.1  | 0.05  | 0.80  | 2   | 964     | 0.8002316    | 5.9914645  | 9.6400000  |
      | G-004 | 0.5  | 0.01  | 0.90  | 6   | 93      | 0.9011611    | 16.8118938 | 23.2500000 |
      | G-020 | 0.3  | 0.10  | 0.80  | 30  | 228     | 0.8013717    | 40.2560237 | 20.5200000 |
      | G-021 | 0.3  | 0.001 | 0.90  | 100 | 865     | 0.9002502    | 149.4493   | 77.8500000 |

    Examples: Küçük N (N < 100, aralık daraltma dalı)
      | id    | w    | alpha | power | df  | n_total | actual_power | critical   | ncp        |
      | G-009 | 0.8  | 0.05  | 0.80  | 1   | 13      | 0.8223816    | 3.8414588  | 8.3200000  |
      | G-010 | 0.9  | 0.05  | 0.95  | 10  | 31      | 0.9563998    | 18.3070381 | 25.1100000 |
      | G-022 | 1.5  | 0.05  | 0.80  | 2   | 5       | 0.8608329    | 5.9914645  | 11.2500000 |

    Examples: Büyük N (N > 100, aralık genişletme dalı)
      | id    | w    | alpha | power | df  | n_total | actual_power | critical   | ncp        |
      | G-011 | 0.05 | 0.05  | 0.95  | 1   | 5198    | 0.9500042    | 3.8414588  | 12.9950000 |
      | G-012 | 0.02 | 0.05  | 0.80  | 3   | 27257   | 0.8000095    | 7.8147279  | 10.9028000 |

    Examples: Sınırlar
      | id    | w        | alpha | power     | df  | n_total    | actual_power | critical   | ncp        |
      | G-007 | 0.3      | 0.05  | 0.05      | 1   | 1          | 0.0603726    | 3.8414588  | 0.0900000  |
      | G-013 | 0.000001 | 0.05  | 0.80      | 1   | 7.8489e+12 | 0.8000000    | 3.8414588  | 7.8488605  |
      | G-017 | 0.3      | 0.05  | 0.9999999 | 1   | 570        | 0.9999999    | 3.8414588  | 51.3000000 |
      | G-019 | 0.3      | 0.05  | 0.80      | 2.5 | 115        | 0.8017509    | 6.9280761  | 10.3500000 |
    # G-007: güç = α kabul edilir; N alt sınır 1'e çekilir, gerçek güç hedefin üstünde kalır.
    # G-013: w alt sınırda (1e-6) kabul edilir; N ekranda yalnızca 5 anlamlı basamakla görünür (A-5).
    # G-017: güç üst sınırda (0.9999999) kabul edilir.
    # G-019: kesirli df kabul edilir ve hesapta aynen kullanılır.

  Scenario: Yuvarlama kuralı — kesirli N 10 basamağa yuvarlanıp yukarı yuvarlanır
    Given a priori aramanın bulduğu kesirli N değeri
    When n_total hesaplanır
    Then n_total = ⌈ ⌊N · 10^10 + 0.5⌋ / 10^10 ⌉ olur
    And actual_power, ncp ve critical, n_total ile yeniden hesaplanır
    # Birim testi: N = 104.00000000003 → 104 ; N = 104.0000001 → 105 ; N = 144.2 → 145

  # ---------- Post hoc ----------

  Scenario Outline: Post hoc modda güç
    Given mod "post-hoc"
    And w <w>, alpha <alpha>, n <n>, df <df>
    When hesaplama yapılır
    Then çıkış kodu 0 olur
    And "power", 1e-6 toleransla <power> olur
    And "critical_chi2", 1e-6 toleransla <critical> olur
    And "ncp", 1e-6 toleransla <ncp> olur

    Examples: G*Power arayüz vektörleri
      | id    | w    | alpha | n      | df | power     | critical   | ncp        |
      | G-005 | 0.3  | 0.05  | 100    | 1  | 0.8508388 | 3.8414588  | 9.0000000  |
      | G-006 | 0.2  | 0.05  | 250    | 3  | 0.7610631 | 7.8147279  | 10.0000000 |
      | G-028 | 0.5  | 0.01  | 30     | 4  | 0.3354524 | 13.2767041 | 7.5000000  |
      | G-029 | 0.3  | 0.05  | 145    | 1  | 0.9507851 | 3.8414588  | 13.0500000 |
      | G-030 | 0.25 | 0.05  | 200    | 6  | 0.7584630 | 12.5915872 | 12.5000000 |

    Examples: Sınırlar
      | id    | w    | alpha | n      | df | power     | critical   | ncp        |
      | G-023 | 0    | 0.05  | 100    | 1  | 0.0500000 | 3.8414588  | 0          |
      | G-025 | 0.3  | 0.05  | 1      | 1  | 0.0603726 | 3.8414588  | 0.0900000  |
      | G-027 | 0.1  | 0.05  | 100000 | 5  | 1.0000000 | 11.0704977 | 1000       |
    # G-023: post hoc'ta w = 0 kabul edilir; λ = 0 ve güç = α.
    # G-029 ↔ G-001 ve G-025 ↔ G-007: a priori ve post hoc aynı N'de aynı gücü verir.

  # ---------- Geçersiz girdiler ----------

  Scenario Outline: Geçersiz girdiler G*Power'ın mesajıyla hata verir
    Given mod "<mode>" ve girdiler <inputs>
    When hesaplama yapılır
    Then çıktı tek satır {"error":"<mesaj>", "code": ..., "field": ...} olur (kod ve alan §0.4)
    And çıkış kodu 2 olur

    Examples: G*Power arayüz vektörleri
      | id    | mode     | inputs                                 | mesaj                                                             |
      | G-008 | a-priori | w=0.3 alpha=0.05 power=0.80 df=0       | Degrees of Freedom must be greater or equal one.                  |
      | G-014 | a-priori | w=0.0000009 alpha=0.05 power=0.80 df=1 | Effect size w must be greater 1e-06.                              |
      | G-015 | a-priori | w=0.3 alpha=0.05 power=0.04 df=1       | Power must be greater than or equal to alpha.                     |
      | G-016 | a-priori | w=0.3 alpha=0.00000001 power=0.80 df=1 | Alpha is outside the admissible range (1e-07, 1).                 |
      | G-018 | a-priori | w=0.3 alpha=0.05 power=0.99999999 df=1 | Power is outside the admissible range (1e-07, 1).                 |
      | G-024 | post-hoc | w=-0.1 alpha=0.05 n=100 df=1           | Effect size w must be non-negative.                               |
      | G-026 | post-hoc | w=0.3 alpha=0.05 n=0 df=1              | Total sample size is outside the admissible range (1, 2147483646) |

  Scenario: Doğrulama sırası — ilk hatalı kontrol raporlanır
    Given mod "a-priori"
    And w 0.0000009, alpha 0.05, power 0.80, df 0
    When hesaplama yapılır
    Then açıklama "Degrees of Freedom must be greater or equal one." olur
    # Kaynak: doğrulama sırası binary'den (L-012); bu birleşik girdi arayüzde ayrıca denenmedi.
```

## 7. Kabul kriterlerinin kapsamı

| Yönerge sınır değeri | Vektörler |
|---|---|
| Etki büyüklüğü çok küçük | G-003 (w = 0.1), G-011 (0.05), G-012 (0.02), G-013 (w = 1e-6, alt sınır), G-014 (alt sınırın altı → hata) |
| Etki büyüklüğü çok büyük | G-009 (0.8), G-010 (0.9), G-022 (1.5) |
| Güç ≤ α | G-007 (güç = α → kabul), G-015 (güç < α → hata), G-023 (post hoc w = 0 → güç = α) |
| Eşit olmayan grup oranı | Uygulanamaz (§1) |
| Geçersiz girdiler | G-008, G-014, G-015, G-016, G-018, G-024, G-026 |
| Diğer sınırlar | G-017 (güç üst sınırı), G-019 (kesirli df), G-021 (df = 100), G-025 (N = 1), G-027 (N = 100 000) |

Toplam: **30 G\*Power arayüz vektörü** (23 başarılı hesap, 7 hata). Kılavuzda bu aile için çalışılmış örnek yoktur (kanıt kaydı L-032). Ölçek için pwr/statsmodels vektörleri test aşamasında eklenecek (yönerge).
