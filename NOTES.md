# NOTES — gpower-clone (χ² olumsallık tablosu, temiz oda yazımı)

Tek davranış kaynağı: `SPEC.md` (şu an v1.2). Başka kaynak açılmadı; tersine mühendislik aracı kullanılmadı.

## Kurulum ve çalıştırma

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[test,diff]"     # Linux/macOS: .venv/bin/python
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
| `src/gpower_clone/cli.py` | İnce katman: argparse → float → motor → tek satır JSON |
| `tests/test_acceptance.py` | SPEC §6 Gherkin; her vektör ayrı test (15 a priori, 8 post hoc, 7 hata + sıra, yuvarlama örnekleri) |
| `tests/test_engine.py`, `tests/test_cli.py` | §4.5 adımları (x dizisi 50.5, 24.75, …), sınırlar, eş adlar, alt süreç (`python -m`, console script) |
| `tests/differential.py` | `oracle/vectors.csv` ↔ CLI (gerçek alt süreç), ekran basamağında karşılaştırma, uyum raporu |
| `tests/fixtures/spec_vectors.csv` | SPEC §6'daki 30 vektörün CSV biçimi (düzeneği kâhin gelmeden sınamak için) |
| `tests/statsmodels_vectors.py` | statsmodels `GofChisquarePower` ile 894 vektör (594 a priori, 300 post hoc) |
| `tests/test_statsmodels.py` | Aynı 894 vektörlük ızgara pytest regresyon testi olarak |
| `tests/reports/` | Üretilen uyum raporları (SPEC vektörleri, statsmodels) |

## Sonuçlar

- pytest: **93 geçti, 1 atlandı** (`oracle/vectors.csv` henüz yok → `test_oracle_gate` atlanıyor).
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
