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
3. **Kök bulma:** [alt, üst] aralığında Brent tarzı bir kök bulucu (ikiye bölme + ters kuadratik/sekant adımları) kullanılır. Tolerans 1e-10, en fazla 300 iterasyon. Uç noktalarda f aynı işaretliyse kök bulunamaz. (L-018, L-020)
4. **Yuvarlama:** Bulunan kesirli N önce 10 ondalık basamağa yuvarlanır: N′ = ⌊N · 10¹⁰ + 0.5⌋ / 10¹⁰. Sonra yukarı yuvarlanır: n_total = ⌈N′⌉. Bu nedenle kesirli kısmı 5·10⁻¹¹'den küçük olan bir N aşağı iner (ör. 104.00000000003 → 104), daha büyük her kesir yukarı çıkar. (L-021)
5. **Alt sınır:** n_total < 1 ise n_total = 1. (L-018; oracle G-007)
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
| A-1 | CLI parametre adları ve çıktı alan adları | Yönergedeki `CONTRACT.md` bağlantısı boş (`[LİNK: CONTRACT.md]`); hocaya Classroom'dan sorulacak. O zamana kadar §2'deki geçici adlar kullanılır. |
| A-2 | JSON'daki ondalık basamak sayısı. Yönerge örneği 4 basamak, G\*Power ekranı çoğunlukla 7 basamak gösteriyor. | A-1 ile birlikte netleşecek. O zamana kadar tam hassasiyet (yuvarlamasız double) üretilir. |
| A-3 | Post hoc'ta N'ye kesirli değer girildiğinde G\*Power'ın davranışı | Gözlenmedi. CLI kesirli N'yi hata olarak reddeder (tasarım kararı). |
| A-4 | Merkezi χ² quantile'ının G\*Power içindeki iç yöntemi | İncelenmedi. §3 toleransı kütüphane quantile'ıyla doğrulanır (30 vektörde kontrol edilecek). |
| A-5 | G-013'te (N ≈ 7.8489·10¹²) N'nin tam tamsayı değeri | Ekran yalnızca 5 anlamlı basamak gösteriyor. Bu vektörde `n_total` ekrandaki gösterim hassasiyetinde karşılaştırılır. KAPI hesabında "tam eşleşmesi doğrulanamayan vektör" olarak raporlanır. |

## 6. Kabul kriterleri

> Değerler `oracle/vectors.csv` dosyasından alınmıştır (G\*Power 3.1.9.7 arayüzü; ekran görüntüleri `oracle/screenshots/`).
> `n_total` tam eşleşmeli. Diğer sayısal alanlar, ekranda gösterilen basamak sayısında eşleşmelidir (§3).

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
    And "actual_power", ekrandaki basamakta <actual_power> olur
    And "critical", ekrandaki basamakta <critical> olur
    And "ncp", ekrandaki basamakta <ncp> olur
    And "df" <df> olur

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
    And "actual_power", ekrandaki basamakta <power> olur
    And "critical", ekrandaki basamakta <critical> olur
    And "ncp", ekrandaki basamakta <ncp> olur
    And "n_total" tam olarak <n> olur

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
    Then çıktı tek satır {"error":"<mesaj>"} olur
    And çıkış kodu sıfırdan farklıdır

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
