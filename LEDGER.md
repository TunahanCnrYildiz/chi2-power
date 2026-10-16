# Kanıt Defteri (LEDGER)

Kapsam: G\*Power 3.1.9.7 · `GPowerNT.exe` (SHA-256 `C63E6A13…EFC812`) · χ² olumsallık tablosu.

## Etiketler

| Etiket | Anlamı | Puan |
|---|---|---|
| `[DOK]` | Kılavuzda ya da makalede yazıyor (sayfa/bölüm belirtilir). | — |
| `[REA]` | Binary'den kanıtlandı: fonksiyon adresi ve/veya dize referansı. | ✔ |
| `[AJAN]` | Ajanın çıkarımı, kanıtı yok. Diferansiyel testle sınanmalı. | — |

Kurallar:
- Her satır **tek bir iddia** içerir ve bir kimliği vardır (`L-001`, `L-002`, …).
- `[REA]` satırı: adres (`0x…`), araç (REA aracı ya da Ghidra), kısa alıntı (en fazla birkaç satır, decompile dökümü değil).
- `[AJAN]` satırı sonradan kanıtlanırsa silinmez; durumu güncellenir ve yeni bir `[REA]` satırına bağlanır.
- `Test` sütunu, iddiayı sınayan oracle vektörünü ya da testi gösterir.
- Yanlış çıkan iddialar `HALLUCINATIONS.md`'ye taşınır.

## Kılavuzda olmayan davranışlar (öncelikli av listesi)

- [x] A priori N araması: başlangıç değeri, adım stratejisi, durma koşulu (L-018, L-019, L-020)
- [x] Yuvarlama: N tamsayıya nasıl getiriliyor (L-021)
- [x] "Actual power" hangi N ile hesaplanıyor (L-022)
- [x] Merkezi olmayan χ² dağılımının hesap yöntemi ve hassasiyeti (L-024)
- [ ] Kritik χ² değerinin hesabı: ters CDF'in iç yöntemi (L-023'te çağrı kanıtlı, quantile fonksiyonunun içi açık)
- [x] Sınırlar: df, w, güç, α, N aralıkları (L-006, L-007, L-013 – L-017)
- [x] Geçersiz girdiye tepki (hata mesajı dizeleri) (L-006, L-007, L-009, L-013 – L-017)
- [x] A priori arama hedef fonksiyonu f(N) (L-027) ve aralık kurma sabitleri (L-028)

## Defter

| ID | Etiket | İddia | Kanıt (adres / dize / kaynak) | Test | Durum |
|---|---|---|---|---|---|
| L-001 | `[AJAN]` | Merkezi olmama parametresi λ = w² · N. | İlk ilkelerden. → L-012 ile kanıtlandı. | G-001 – G-007 | kanıtlı (bkz. L-012) |
| L-002 | `[REA]` | `GPowerNT.exe` 32-bit x86 PE32 görüntüsüdür; kaynak tablosunda RT_DLGINIT ve RT_TOOLBAR türleri bulunur (MFC uygulaması izi). | REA `inspect_pe_resources`, Evidence `ev_68f5a69b…0bd641`: machine `0x14c`, 144 kaynak, kapsam tam. | — | kanıtlı |
| L-003 | `[AJAN]` | χ² olumsallık hesabı `PowerChiCont` sınıfında, `PowerChi` → `PowerAnalysis` hiyerarşisi altında. | Ön tarama: RTTI dizeleri. → Sınıf L-011 ile kanıtlandı; üst sınıf hiyerarşisi hâlâ doğrulanmadı. | — | kısmen kanıtlı (bkz. L-011) |
| L-004 | `[AJAN]` | χ² CDF/quantile hesapları DCDFLIB tarzı bir kök arama kütüphanesiyle yapılıyor. | Ön tarama: hata metinlerinin benzerliği. → Kısmen L-008 ve L-009 ile kanıtlandı. | — | kısmen kanıtlı (bkz. L-008, L-009) |
| L-005 | `[AJAN]` | df < 1 ve güç < α geçersiz girdidir. | Ön tarama. → L-006, L-007 ve L-012 ile kanıtlandı. | G-007, G-008 | kanıtlı |
| L-006 | `[REA]` | df doğrulaması: df ≥ 1.0 ise geçerli, aksi hâlde "Degrees of Freedom must be greater or equal one." hatası. df **ondalık (double)** olarak karşılaştırılıyor; tamsayı kontrolü bu fonksiyonda yok (oracle G-019: df = 2.5 kabul edilip hesaplanıyor). χ² olumsallık yönlendiricisi (L-012) her modda önce bu kontrolü çağırır. | `FUN_00487800` (`0x487800`–`0x48782d`); dize `0x5c615c`, referans `0x48781b`; çağıran `FUN_00498ad0`. Ghidra (REA CLI `trace` + `function`), Evidence `ev_3fa58546…f4ed54`, `ev_d88d66f1…191fc1`. Alıntı: `if (1.0 <= param_1) return 1;` | G-008 (aynı mesaj) | kanıtlı |
| L-007 | `[REA]` | Güç doğrulaması: α ≤ güç ise geçerli; yani **güç = α kabul edilir**, yalnızca güç < α reddedilir ("Power must be greater than or equal to alpha."). Birinci argüman α, ikincisi güçtür (L-012'deki çağrı sırası). | `FUN_004880e0` (`0x4880e0`–`0x48810b`); dize `0x5c6220`, referans `0x4880f9`. Evidence `ev_ae423af3…3303ea`, `ev_371dc388…c6a5eb`. Alıntı: `if (param_1 <= param_2) return 1;` | G-007 (güç = α → hata yok) | kanıtlı |
| L-008 | `[REA]` | χ² CDF sarmalayıcısı, merkezi olmama parametresi `< 1e-100` ise merkezi χ² yoluna, aksi hâlde ayrı bir merkezi olmayan χ² CDF fonksiyonuna (`FUN_0043e7e0`) gider. Girdi x, nesnedeki bir ölçek çarpanıyla (`+0x20`) çarpılır. | `FUN_0043eca0` (`0x43eca0`–`0x43eed0`); dizeler `0x5c3d98`–`0x5c3e40`, "below lower search bound" referansı `0x43ee97`. Evidence `ev_843fa197…1c5cce`, `ev_bfcbb250…6d3e34`. Alıntı: `if (1e-100 <= dVar1) { … FUN_0043e7e0(…) }` | — | kanıtlı |
| L-009 | `[REA]` | χ² CDF durum kodları DCDFLIB sözleşmesini izler: `<0` parametre aralık dışı, `1` alt arama sınırının altında, `2` üst sınırın üstünde, `3` p + q ≠ 1, diğerleri bilinmeyen hata. Her durumda C++ istisnası fırlatılır (`_CxxThrowException`). Merkezi dalda çağrı imzası 7 argümanlı (`which, p, q, x, df, status, bound` düzeni). | `FUN_0043eca0`, durum dalları ve `VCRUNTIME140.DLL::_CxxThrowException` çağrıları. Evidence `ev_bfcbb250…6d3e34`. | geçersiz girdi testleri | kanıtlı (argüman adları [AJAN] yorumudur) |
| L-010 | `[REA]` | "Goodness-of-fit tests: Contingency tables" adı, doğrudan çağıranı olmayan küçük bir fonksiyonda bir dize nesnesine kopyalanır (sanal metot olarak çağrılan bir "test adı" fonksiyonu olması muhtemel). | `FUN_00498990` (`0x498990`–`0x4989ff`); dize `0x5c6dd4`, referans `0x4989ca`. Evidence `ev_88626922…394491`, `ev_e89f3c41…8dc4ae`. Çağıran listesi boş. → `PowerChiCont` sanal tablosunun `+0x78` yuvası (`0x5c6b8c`), Evidence `ev_266e6cef…d88c60`. | — | kanıtlı |
| L-011 | `[REA]` | `PowerChiCont` sınıfının sanal tablosu `0x5c6b14`'te başlar (`0x5c6c38`'de biter). Tablodan önceki `0x5c6b10` adresi RTTI Complete Object Locator'a (`0x5ee8b8`) işaret eder; onun tip tanımlayıcısı (`0x60c8d8`) `.?AVPowerChiCont@@` adını taşır. | REA `read-bytes`: `0x5c6b10`–`0x5c6c3c` (Evidence `ev_f6067f8b…af454b`, `ev_62d64fa2…bbc7a8`), COL `0x5ee8b8` (`ev_d6c728db…c35447`), tip adı `0x60c8e0` (`ev_a9f1e01d…0bcfe7`). | — | kanıtlı |
| L-012 | `[REA]` | χ² olumsallık analiz yönlendiricisi (vtable `+0xc8`) önce df'yi okuyup doğrular (L-006), sonra analiz türüne göre dallanır. **Tür 0 = a priori:** w, α, güç okunur; w ≥ 1e-6 (L-016), α (L-013), güç (L-014), α ≤ güç (L-007) kontrol edilir; vtable `+0x48` çağrılır (yuvarlama bayrağı = 1). **Tür 2 = post hoc:** w, α, N okunur; w ≥ 0 (L-017), α, N ∈ [1, 2147483646] (L-015) kontrol edilir; vtable `+0x30` çağrılır. df her iki modda nesneye ve χ² dağılım nesnesine yazılır. (Tür 1, 3, 4 sırasıyla sensitivity, criterion ve compromise; kapsam dışı.) | `FUN_00498ad0` (`0x498ad0`), vtable yuvası `0x5c6bdc`. Evidence `ev_23ba9196…27d6dc`. | G-001 – G-008 | kanıtlı |
| L-013 | `[REA]` | α geçerli aralığı: 1e-7 ≤ α ≤ 0.9999999; dışında "Alpha is outside the admissible range (" hatası. | `FUN_00487530` (`0x487530`). Evidence `ev_33e350fb…1d7787`. Alıntı: `if ((1e-07 <= param_1) && (param_1 <= 0.9999999)) return 1;` | G-016 (mesaj: "…(1e-07, 1).") | kanıtlı + oracle |
| L-014 | `[REA]` | Güç geçerli aralığı: 1e-7 ≤ güç ≤ 0.9999999; dışında "Power is outside the admissible range (" hatası. | `FUN_00488110` (`0x488110`). Evidence `ev_2fe3ced9…a0face`. | G-017 (0.9999999 kabul), G-018 (0.99999999 → hata) | kanıtlı + oracle |
| L-015 | `[REA]` | Post hoc'ta N tamsayı olarak okunur; geçerli aralık 1 ≤ N ≤ 2147483646; dışında "Total sample size is outside the admissible range (" hatası. | `FUN_00488a10` (`0x488a10`), çağrı `FUN_00488a10(N, 1, 0x7ffffffe)` (L-012). Evidence `ev_0d2d2ab0…7e065f`. | G-025 (N = 1 kabul), G-026 (N = 0 → hata), G-027 (N = 100000) | kanıtlı + oracle |
| L-016 | `[REA]` | A priori'de w < 1e-6 ise "Effect size w must be greater 1e-06" türünde hata; w = 1e-6 kabul edilir. | `FUN_00487880` (`0x487880`), çağrıda ad "w" ve sınır `0x3eb0c6f7a0b5ed8d` (= 1e-6). Evidence `ev_d846a5d1…911ea3`. | G-013 (w = 1e-6 kabul), G-014 (mesaj: "Effect size w must be greater 1e-06.") | kanıtlı + oracle |
| L-017 | `[REA]` | Post hoc'ta yalnızca w < 0 reddedilir ("Effect size w must be non-negative."); w = 0 kabul edilir. | `FUN_00487970` (`0x487970`). Evidence `ev_e6e5e71f…d9315d`. | G-023 (w = 0 kabul, güç = α), G-024 (w = −0.1 → hata) | kanıtlı + oracle |
| L-018 | `[REA]` | A priori N hesabı: (1) arama aralığı kurulur (L-019), (2) kök bulucu tolerans 1e-10 ve en fazla 300 iterasyonla N'yi bulur (L-020), (3) yuvarlama bayrağı açıksa N yuvarlanır (L-021), (4) N alt sınırın (1) altındaysa alt sınıra çekilir, (5) gerçek güç bu N ile post hoc fonksiyonundan hesaplanır (L-022). | `FUN_00496aa0` (`0x496aa0`), vtable `+0x48` (`0x5c6b5c`). Evidence `ev_34bb74a6…c4b75b`. Sabitler: `0x3ddb7cdfd9d7bdbb` (= 1e-10), `300`. | G-001 – G-004, G-007 | kanıtlı |
| L-019 | `[REA]` | Arama aralığı alt sınır 1, başlangıç 100 ile kurulur. f(100) < 0 ise üst sınır f ≥ 0 olana kadar 1.6 ile çarpılır (100, 160, 256, …) ve alt sınır bir önceki değer olur. f(100) ≥ 0 ise aralık 1'e doğru daraltılır. Alt sınır hiçbir zaman 1'in altına inmez. | `FUN_00499150` → `FUN_004962d0(1.0, 100.0)` (`0x4962d0`). Evidence `ev_0375f101…a7db26`, `ev_b4e96ae2…95ecbf`. Daraltma dalının ayrıntısı ve sabitler: L-028. | G-003 (N = 964 > 100), G-004 (N = 93), G-007 (N = 1) | kanıtlı |
| L-020 | `[REA]` | Kök bulucu Brent tarzı bir yöntemdir (ikiye bölme + ters kuadratik/sekant adımları). Aralık uçlarında f aynı işaretliyse durum 1 ile 0 döner; iterasyon sınırı (300) dolarsa durum 2 ile son tahmin döner; |yarım aralık| ≤ |b|·1.11e-16 olunca durur. | `FUN_004f9bb0` (`0x4f9bb0`). Evidence `ev_2a146f76…dab95b`. Sabit `1.1102230246251565e-16`. | — | kanıtlı; yöntemin adı [AJAN] yorumu |
| L-021 | `[REA]` | N yuvarlaması: N önce 10 ondalık basamağa yuvarlanır (`floor(N·1e10 + 0.5) / 1e10`), sonra yukarı yuvarlanır (`ceil`). Sonuç: kesirli kısmı 5·10⁻¹¹'den küçük olan N aşağı iner (ör. 104.00000000003 → 104); daha büyük her kesir yukarı çıkar. | `FUN_00496a20` (`0x496a20`), vtable `+0x74` (`0x5c6b88`). Evidence `ev_b16a2514…dc439a`. | G-001 – G-004 | kanıtlı |
| L-022 | `[REA]` | A priori'de ekrandaki "Actual power", yuvarlanmış (ve alt sınıra çekilmiş) N ile post hoc fonksiyonu çağrılarak hesaplanır. | `FUN_00496aa0`, vtable `+0x30` çağrısı, sonuç `+0x108` alanına yazılır. Evidence `ev_34bb74a6…c4b75b`. | G-001 – G-004, G-007 | kanıtlı |
| L-023 | `[REA]` | Post hoc güç: χ² dağılımı merkezi yapılır (λ = 0), kritik değer = merkezi χ²(df) dağılımının 1 − α quantile'ı; sonra λ (L-012 → `+0x50`) atanır ve güç = 1 − CDF_λ(kritik). λ = w² · N. | `FUN_004981d0` (`0x4981d0`, vtable `+0x30`); λ: `FUN_00498770` (`0x498770`, vtable `+0x50`). Evidence `ev_cd45bcf5…c90a9f`, `ev_79557ba9…2f9f03`. Alıntı: `return param_1 * param_1 * N;` | G-005, G-006 (λ = 9, 10) | kanıtlı |
| L-024 | `[REA]` | Merkezi olmayan χ² CDF'i, Poisson ağırlıklı merkezi χ² terimlerinin toplamıdır. Toplama k = ⌊λ/2⌋ teriminden başlar, önce ileri sonra geri ilerler; eklenen terim ≤ toplam × 2.220446e-16 olunca durur. Özel durumlar: x NaN → x; x = +∞ → 1; df < 0 veya λ < 0 → NaN; x ≤ 0 → 0. | `FUN_0043e7e0` (`0x43e7e0`). Evidence `ev_063d699f…418b78`. Sabit `2.220446049250313e-16`. | G-001 – G-007 (güç değerleri) | kanıtlı; "Ding/Benton–Krishnamoorthy benzeri" yorumu [AJAN] |
| L-025 | `[AJAN]` | A priori kök bulucunun hedef fonksiyonu f(N) = güç(N) − hedef güç'tür (N sürekli/kesirli olarak değerlendirilir). | İlk ilkelerden ve L-019'daki işaret mantığından. → L-027 ile kanıtlandı. | G-001 – G-004 | kanıtlı (bkz. L-027) |
| L-026 | `[AJAN]` | L-019'daki daraltma dalı (f(100) ≥ 0 olduğunda, yani N < 100) aralığı yarılayarak 1'e yaklaştırır. | Decompile çıktısındaki ifade (`(m + 1)·0.5 − 1`) beklenen yarılama formülüyle tutarsız göründüğü için ajan decompile hatası varsaydı. → **Yanlış çıktı:** montaj (L-028) ifadenin gerçek olduğunu gösterdi; adım standart yarılama değil. Bkz. HALLUCINATIONS H-001. | N < 100 vektörleri (G-004: N = 93, G-007: N = 1) | çürütüldü → L-028 |
| L-027 | `[REA]` | A priori kök bulucunun hedef fonksiyonu f(N) = güç(w, α, N) − hedef güç'tür. Güç, post hoc fonksiyonuyla (L-023) **kesirli N** ile hesaplanır; yuvarlama aramadan sonra yapılır (L-021). Kök bulucu ve aralık kurucu aynı nesne üzerinden çağrılır; hedef, sanal `+4` yuvasındaki yönlendiriciden (`+0x2ac` alanı = 0 → a priori) `+0x11c` yuvasına gider. | Yönlendirici `FUN_00496830` (`0x496830`, vtable `+4`), hedef `FUN_004968d0` (`0x4968d0`, vtable `+0x11c`). Evidence `ev_3c802159…7fbf4a`, `ev_dd99599a…823149`. Alıntı: `return posthoc(w, alpha, N) - target_power;` (sadeleştirilmiş). A priori'nin `ECX = this` ile çağrıldığı montajdan: `0x496aeb: MOV ECX, ESI`, `0x496b03: CALL 0x004f9bb0` (`ev_34bb74a6…c4b75b`). | G-001 – G-004, G-007 | kanıtlı |
| L-028 | `[REA]` | Arama aralığı kurma (L-019) ayrıntısı, montaj ve sabitlerle: başlangıç x₀ = 100, alt sınır a = 1. **f(100) < 0:** alt = 100, üst = 160; f(üst) < 0 olduğu sürece alt ← üst, üst ← üst × 1.6. **f(100) ≥ 0:** üst = 100, x = (a + 100) × 0.5 = 50.5; x ≥ a ve f(x) > 0 olduğu sürece üst ← x, x ← (x + a) × 0.5 − a (yani a = 1 için 24.75, 11.875, 5.4375, 2.21875, 0.609…). Döngü bitince alt ← x; alt < a ise alt ← a. Sonra kök bulucu [alt, üst] aralığında çalışır. | `FUN_004962d0` montajı `0x49638f`–`0x496407` (`ev_b4e96ae2…95ecbf`). Sabitler REA `read-bytes`: `0x5c29a8` = 0.5, `0x5c29c0` = 0.0 (`ev_5431cafb…2f1aa8`); `0x5c4ad8` = 1.6 (`ev_3ecf46dd…994907`); `0x5c3f48` = 1e-10 (kök bulucu toleransı, `ev_4889d761…e875c1`). Alıntı: `0x4963ec: ADDSD XMM0, XMM1` / `0x4963f0: MULSD XMM0, [0x005c29a8]` / `0x4963f8: SUBSD XMM0, XMM1`. | G-004 (N = 93), G-007 (N = 1), G-009/G-010 (planlandı) | kanıtlı |

| L-029 | `[DOK]` | A priori analizde N; güç (1 − β), α ve etki büyüklüğünün fonksiyonu olarak hesaplanır. Post hoc analizde güç; α, etki büyüklüğü ve N'nin fonksiyonu olarak hesaplanır. | G\*Power 3.1 kılavuzu (1 Haziran 2023), s. 2, §1.1 "Types of power analysis" (madde 1 ve 4). | G-001 – G-030 | belgeli |
| L-030 | `[DOK]` | A priori analizde kesirli örneklem büyüklükleri **her zaman yukarı yuvarlanır**; bu nedenle gerçek güç çoğu zaman istenen güçten biraz yüksektir. | Kılavuz s. 4, §1.2 (a priori örneği sonrası açıklama). **Kılavuzda olmayan ayrıntı:** binary, yukarı yuvarlamadan önce N'yi 10 ondalık basamağa yuvarlar (L-021); kesirli kısmı 5·10⁻¹¹'den küçük N bu nedenle aşağı iner. Kılavuzdaki "her zaman yukarı" ifadesi bu sınır durumunda geçerli değildir. | G-001 – G-004, G-009 – G-012 | belgeli; ayrıntı [REA] L-021 |
| L-031 | `[DOK]` | G\*Power hesaplayıcısı merkezi ve merkezi olmayan χ² dağılım fonksiyonları (CDF, PDF, quantile) sunar. | Kılavuz s. 7, §2 "The G\*Power calculator" (chi2cdf / chi2inv / ncx2cdf / ncx2inv listesi). | — | belgeli |
| L-032 | `[DOK]` | Kılavuzda "χ² tests → Goodness-of-fit tests: Contingency tables" için **ayrı bir bölüm, etki büyüklüğü tanımı ya da çalışılmış örnek yoktur**; kılavuz kendini "henüz tamamlanmamış" olarak tanımlar. Bu nedenle bu ailenin davranışı yalnızca binary (`[REA]`) ve arayüz (oracle) üzerinden belirlenebilir; "kılavuz örnekleri" bu aile için mevcut değildir. | Kılavuz s. 1 (içindekiler ve giriş notu); tam metinde "contingency" yalnızca s. 17'de Fisher testi bağlamında geçer. Kılavuz dosyası SHA-256 `cde1293c…ec40c8249f`. | — | belgeli (yokluk) |

## Evidence dizini

Defterde kısaltılmış Evidence kimliklerinin tam hâli (REA çıktıları; ham JSON dosyaları decompile içerdiği için repoda değil, `re-work/` altında).

| Evidence | REA işlemi |
|---|---|
| `ev_0375f10162d3c4a2df9dd389c0a347285f56ce67c5d050ec1a108a08eba7db26` | analyze_function |
| `ev_063d699f76105a3c0fe20dfe4f4c207fa40d37d81ff928fb130b2b92b3418b78` | analyze_function |
| `ev_0d2d2ab055ed798549ee1d4b01b23d2f220d10e61ec0b60a73b72de0967e065f` | analyze_function |
| `ev_23ba919608e67d6931457fb7963bd09492c3cff9eac073c492e75b4fca27d6dc` | analyze_function |
| `ev_266e6cefe2bf32c8fd2a3280df892ff93aa87563727ded846b37dc8775d88c60` | xrefs |
| `ev_2a146f7690a4c9c6ea25ddb774d54ba8a27de28310f60b0b9659ad43aadab95b` | analyze_function |
| `ev_2fe3ced98cc5281687ef9a4fd7f0b841cb88674677aaa610797f7e77f5a0face` | analyze_function |
| `ev_33e350fbb8a3f2b689fbda6efbfb708b6574d701cf0bbd88ca7a6afb2f1d7787` | analyze_function |
| `ev_34bb74a6432cfb5829ccc08b88c0af8ec36f5b41bba57487c4edb0bd24c4b75b` | analyze_function |
| `ev_371dc38821a28b5a96e6779d888a8191fc2de1fc1b4be5423b7fac671fc6a5eb` | analyze_function |
| `ev_3c80215921a93bc4b474d124e82cb42174a615a7714afcccfaf94d26cc7fbf4a` | analyze_function |
| `ev_3ecf46dd789292c9f4a7324337f9b3bba2194d49686e361a60c9ef4910994907` | read_bytes |
| `ev_3fa5854651ddd4fb4f3b1a9b2af418c6b9e883183f5265b58a73af6e92f4ed54` | trace_feature |
| `ev_4889d761734a2f5b4deb657c364a559a9b67000e298eb62348c87b2df7e875c1` | read_bytes |
| `ev_5431cafb01db234a082b39015f59e050a00e4d0a1a9f6b1045d5a3648d2f1aa8` | read_bytes |
| `ev_62d64fa2f2a6cf8f81878e9538b7c973f4f82a702093cdccc4a1a214d5bbc7a8` | read_bytes |
| `ev_68f5a69be943e1eac8081af62a1cef18c34244379d357618199d1d15460bd641` | inspect_pe_resources |
| `ev_79557ba9a6330ae58fa5b57dea501bdf820e34fcd494dde599d57cf6a72f9f03` | analyze_function |
| `ev_843fa197b363cb9a75614ef0d572a53f2cc4b4567af51855bdf971cc3a1c5cce` | trace_feature |
| `ev_88626922ae266fc889ad471b7bf8f2d231d69597c2ce1a8180a1220ec9394491` | trace_feature |
| `ev_a9f1e01ddfa33790f10c0465b5018db638f3de45c23ec6fc5b65e5cbb00bcfe7` | read_bytes |
| `ev_ae423af33a50bf32a0c339ce8d5811e93f21e11c98a1c0d0811e7a77ce3303ea` | trace_feature |
| `ev_b16a25141af9c8cd32d74551bd6bfc412bdf631ebc577cbe0fcc028436dc439a` | analyze_function |
| `ev_b4e96ae28c5def5328523a84bb7891694e6ab7ce0675068db08c8df95895ecbf` | analyze_function |
| `ev_bfcbb250ad539c1a608175b6a023e16cafe10c844aaa7a6ca61b836bb96d3e34` | analyze_function |
| `ev_cd45bcf5e6905a4f52b2d68172e548840c23a9f648a39db63a5f646d05c90a9f` | analyze_function |
| `ev_d6c728db5e4af3ae9b009c46bcfd6e3e2e1a08e5d743cb5fd46739b0d1c35447` | read_bytes |
| `ev_d846a5d1a48745fc7c7913773226cf53ba438325288602ef42a29db5e1911ea3` | analyze_function |
| `ev_d88d66f1d979bd9fd6bd5faad6eb33d9af797e3eddfed53b0a63f02e91191fc1` | analyze_function |
| `ev_dd99599aec2406402439f00c322b2ebe5ae5ce799346f3d14fa9c35cf2823149` | analyze_function |
| `ev_e6e5e71f50228a62eaa19704ebd43f68a67d22eb57228b3052edf711fed9315d` | analyze_function |
| `ev_e89f3c41aeab8bbdffecb29df146e1d352b72c7c0ec342a6f253ef459b8dc4ae` | analyze_function |
| `ev_f6067f8bdba13751ea31807e87a5555ef19f6db31a338781ddae1037c5af454b` | read_bytes |
