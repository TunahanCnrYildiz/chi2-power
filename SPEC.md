# SPEC · χ² olumsallık tablosu güç analizi

> Bu belge Oturum 2'nin (yazım) göreceği **tek davranış kaynağıdır**.
> Decompile çıktısı, adres ya da kod alıntısı içermez; yalnızca gözlenebilir davranış, algoritmanın özü ve kabul kriterleri.
> Her kuralın sonunda dayandığı kanıt kaydı belirtilir: `(L-0xx)`. Kayıtlar inceleme oturumunun kanıt defterindedir; Oturum 2'nin onları görmesi gerekmez.

- Sürüm: 1.0 taslak · 2026-10-16
- Referans davranış: G\*Power 3.1.9.7 (Windows), "χ² tests → Goodness-of-fit tests: Contingency tables"
- Beklenen değerlerin kaynağı (kâhin): `oracle/vectors.csv` (G\*Power arayüzü, ekran görüntülü). Bu belgedeki sayılar oradan alınmıştır; hiçbiri ajan tarafından üretilmemiştir.

---

## 1. Kapsam

| Konu | Karar |
|---|---|
| Test | χ² testi, olumsallık tablosu; CLI etiketi `chi2-contingency` |
| Modlar | `a-priori` (toplam N hesapla), `post-hoc` (güç hesapla) |
| Kapsam dışı | Sensitivity, criterion, compromise modları (G\*Power'da var, ödev kapsamında değil) (L-012) |
| Grup oranı | **Uygulanamaz.** Bu test tek bir toplam örneklem büyüklüğü (N) kullanır; n1/n2 ya da grup oranı parametresi yoktur. Yönergedeki "eşit olmayan grup oranı" sınır değeri bu aile için tanımsızdır. (L-012) |

## 2. Girdiler

> ⚠️ **CLI parametre adları geçicidir.** Kesin adlar ödevin `CONTRACT.md` belgesinden gelecek; belge geldiğinde yalnızca bu tablo ve §6'daki komut örnekleri güncellenir.

| Kavram | Geçici CLI adı | Tip | Mod | Geçerli aralık | Kaynak |
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
- Açıklamada G\*Power'ın mesajı kullanılmalı (L-006, L-007, L-013 – L-017):

| Durum | Mesaj |
|---|---|
| df < 1 | `Degrees of Freedom must be greater or equal one.` |
| güç < α | `Power must be greater than or equal to alpha.` |
| α aralık dışı | `Alpha is outside the admissible range (…)` |
| güç aralık dışı | `Power is outside the admissible range (…)` |
| N aralık dışı | `Total sample size is outside the admissible range (…)` |
| a priori, w < 1e-6 | `Effect size w must be greater …` |
| post hoc, w < 0 | `Effect size w must be non-negative.` |

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
- **Tolerans** (yönerge): `n_total` **tam** eşleşmeli. Diğer alanlar G\*Power'ın ekranda gösterdiği basamağa kadar eşleşmeli; bu ekranda 7 ondalık basamaktır (ör. `0.9507851`, `3.8414588`, `13.0500000`). Uygulama değerleri en az 7 ondalık basamak doğrulukla üretmelidir.

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
3. **Kök bulma:** [alt, üst] aralığında Brent tarzı bir kök bulucu (ikiye bölme + ters kuadratik/sekant adımları) kullanılır. Tolerans 1e-10, en fazla 300 iterasyon. Uç noktalarda f aynı işaretliyse kök bulunamaz. (L-018, L-020)
4. **Yuvarlama:** Bulunan kesirli N önce 10 ondalık basamağa yuvarlanır: N′ = ⌊N · 10¹⁰ + 0.5⌋ / 10¹⁰. Sonra yukarı yuvarlanır: n_total = ⌈N′⌉. Bu nedenle kesirli kısmı 5·10⁻¹¹'den küçük olan bir N aşağı iner (ör. 104.00000000003 → 104), daha büyük her kesir yukarı çıkar. (L-021)
5. **Alt sınır:** n_total < 1 ise n_total = 1. (L-018; oracle G-007)
6. **Çıktılar:** actual_power, ncp ve critical, **yuvarlanmış** n_total ile hesaplanır (§4.1 – §4.3). (L-022)

> **Neden önemli?** pwr (R) ve statsmodels (Python) N'yi kesirli verir; G\*Power ise 4. adımdaki kuralla tamsayıya çevirir. İki kaynak arasındaki farklar diferansiyel test raporunda bu kurala bağlanarak açıklanmalıdır. (yönerge, kâhin notu)

### 4.6 Sayısal sınırlar
- Güç = α geçerli bir girdidir. Bu durumda çok küçük bir N bulunur ve alt sınır kuralı (§4.5/5) devreye girebilir. Örneğin G-007'de n_total = 1 ve gerçek güç hedefin üstündedir. (L-007, L-018)
- df ondalık olarak karşılaştırılır; kesirli df (ör. 2.5) G\*Power'ın doğrulamasından geçer. Kesirli df ile hesap davranışı oracle vektörü G-019 ile doğrulanacak. (L-006)

## 5. Bilinen açık noktalar

Bunlar Oturum 2'nin varsayım yapmaması gereken konulardır; bir uyuşmazlık çıkarsa test raporunda açıklanmalıdır.

| # | Konu | Durum |
|---|---|---|
| A-1 | CLI parametre ve çıktı alan adları | `CONTRACT.md` bekleniyor |
| A-2 | JSON'daki ondalık basamak sayısı (yönerge örneği 4 basamak, G\*Power ekranı 7 basamak gösteriyor) | `CONTRACT.md`/hoca ile netleşecek; o zamana kadar tam hassasiyet üretilir |
| A-3 | Post hoc N'ye kesirli değer girildiğinde G\*Power davranışı | Gözlenmedi; CLI kesirli N'yi hata olarak reddeder (tasarım kararı) |
| A-4 | Merkezi χ² quantile'ının G\*Power içindeki iç yöntemi | İncelenmedi; §3 toleransı kütüphane quantile'ıyla doğrulanır |

## 6. Kabul kriterleri

> Değerler `oracle/vectors.csv` dosyasından alınmıştır (G\*Power 3.1.9.7 arayüzü, ekran görüntüleri `oracle/screenshots/`).
> `n_total` tam eşleşmeli; diğer sayısal alanlar 7 ondalık basamakta eşleşmeli.

```gherkin
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
    And "actual_power" 7 ondalık basamakta <actual_power> olur
    And "critical" 7 ondalık basamakta <critical> olur
    And "ncp" 7 ondalık basamakta <ncp> olur
    And "df" <df> olur

    Examples: G*Power arayüz vektörleri
      | id    | w   | alpha | power | df | n_total | actual_power | critical   | ncp        |
      | G-001 | 0.3 | 0.05  | 0.95  | 1  | 145     | 0.9507851    | 3.8414588  | 13.0500000 |
      | G-002 | 0.3 | 0.05  | 0.80  | 4  | 133     | 0.8013043    | 9.4877290  | 11.9700000 |
      | G-003 | 0.1 | 0.05  | 0.80  | 2  | 964     | 0.8002316    | 5.9914645  | 9.6400000  |
      | G-004 | 0.5 | 0.01  | 0.90  | 6  | 93      | 0.9011611    | 16.8118938 | 23.2500000 |

  Scenario: Sınır değer — güç α'ya eşit (kabul edilir, N alt sınıra çekilir)
    Given mod "a-priori"
    And w 0.3, alpha 0.05, power 0.05, df 1
    When hesaplama yapılır
    Then çıkış kodu 0 olur
    And "n_total" tam olarak 1 olur
    And "actual_power" 7 ondalık basamakta 0.0603726 olur
    And "critical" 7 ondalık basamakta 3.8414588 olur
    And "ncp" 7 ondalık basamakta 0.0900000 olur

  Scenario: Yuvarlama kuralı — kesirli N 10 basamağa yuvarlanıp yukarı yuvarlanır
    Given a priori aramanın bulduğu kesirli N değeri
    When n_total hesaplanır
    Then n_total = ⌈ ⌊N · 10^10 + 0.5⌋ / 10^10 ⌉ olur
    And actual_power, n_total ile yeniden hesaplanır
    # Birim testi: N = 104.00000000003 → 104 ; N = 104.0000001 → 105 ; N = 144.2 → 145

  # ---------- Post hoc ----------

  Scenario Outline: Post hoc modda güç
    Given mod "post-hoc"
    And w <w>, alpha <alpha>, n <n>, df <df>
    When hesaplama yapılır
    Then çıkış kodu 0 olur
    And "actual_power" 7 ondalık basamakta <power> olur
    And "critical" 7 ondalık basamakta <critical> olur
    And "ncp" 7 ondalık basamakta <ncp> olur
    And "n_total" tam olarak <n> olur

    Examples: G*Power arayüz vektörleri
      | id    | w   | alpha | n   | df | power     | critical  | ncp        |
      | G-005 | 0.3 | 0.05  | 100 | 1  | 0.8508388 | 3.8414588 | 9.0000000  |
      | G-006 | 0.2 | 0.05  | 250 | 3  | 0.7610631 | 7.8147279 | 10.0000000 |

  # ---------- Geçersiz girdiler ----------

  Scenario: df sıfır
    Given mod "a-priori"
    And w 0.3, alpha 0.05, power 0.80, df 0
    When hesaplama yapılır
    Then çıktı {"error":"Degrees of Freedom must be greater or equal one."} olur
    And çıkış kodu sıfırdan farklıdır

  Scenario Outline: Aralık dışı girdiler hata verir
    Given mod "<mode>" ve girdiler <inputs>
    When hesaplama yapılır
    Then çıktıda "error" alanı bulunur ve açıklama "<mesaj_başı>" ile başlar
    And çıkış kodu sıfırdan farklıdır

    Examples: Kurallar binary'den (L-007, L-013 – L-017); G*Power vektörleri G-014 – G-026 ile doğrulanacak
      | mode     | inputs                                  | mesaj_başı                                     |
      | a-priori | w=0.3 alpha=0.05 power=0.04 df=1        | Power must be greater than or equal to alpha. |
      | a-priori | w=0.0000009 alpha=0.05 power=0.8 df=1   | Effect size w must be greater                  |
      | a-priori | w=0.3 alpha=0.00000001 power=0.8 df=1   | Alpha is outside the admissible range          |
      | a-priori | w=0.3 alpha=0.05 power=0.99999999 df=1  | Power is outside the admissible range          |
      | post-hoc | w=-0.1 alpha=0.05 n=100 df=1            | Effect size w must be non-negative.            |
      | post-hoc | w=0.3 alpha=0.05 n=0 df=1               | Total sample size is outside the admissible range |

  Scenario: Doğrulama sırası — ilk hatalı kontrol raporlanır
    Given mod "a-priori"
    And w 0.0000009, alpha 0.05, power 0.80, df 0
    When hesaplama yapılır
    Then açıklama "Degrees of Freedom must be greater or equal one." olur
```

## 7. Kabul kriterlerinin kapsamı

| Yönerge sınır değeri | Senaryo |
|---|---|
| Etki büyüklüğü çok küçük | G-003 (w = 0.1); planlanan G-011 – G-013 |
| Etki büyüklüğü çok büyük | planlanan G-009, G-010, G-022 |
| Güç ≤ α | "güç α'ya eşit" senaryosu (G-007); güç < α hata senaryosu |
| Eşit olmayan grup oranı | Uygulanamaz (§1) |
| Geçersiz girdiler | df = 0 (G-008); aralık dışı girdiler tablosu |

Planlanan vektörler (G-009 – G-030) toplandıkça yukarıdaki `Examples` tablolarına eklenecek.
