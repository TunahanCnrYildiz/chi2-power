# NOTES — gpower-clone (χ² olumsallık tablosu, temiz oda yazımı)

Tek davranış kaynağı: `SPEC.md`. Başka kaynak açılmadı; tersine mühendislik aracı kullanılmadı.

## Kurulum ve çalıştırma

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[test,diff]"     # Linux/macOS: .venv/bin/python
```

```bash
gpower-clone --test chi2-contingency --mode a-priori --w 0.3 --alpha 0.05 --power 0.95 --df 1
# {"n_total":145,"actual_power":0.9507851454132252,"critical":3.8414588206941285,"df":1.0,"ncp":13.049999999999999}
python -m gpower_clone --test chi2-contingency --mode post-hoc --w 0.3 --alpha 0.05 --n 100 --df 1
```

Testler ve raporlar:

```bash
.venv/Scripts/python -m pytest -q                                  # kabul + birim + CLI + düzenek testleri
.venv/Scripts/python tests/differential.py --report reports/differential_report.md          # oracle/vectors.csv
.venv/Scripts/python tests/differential.py --csv tests/fixtures/spec_vectors.csv --report reports/differential_report_spec.md
.venv/Scripts/python tests/statsmodels_vectors.py                   # reports/statsmodels_{report.md,vectors.csv}
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

## Sonuçlar

- pytest: **79 geçti, 1 atlandı** (`oracle/vectors.csv` henüz yok → `test_oracle_gate` atlanıyor).
- SPEC vektörleri üzerinde diferansiyel rapor (`reports/differential_report_spec.md`): 30/30 vektör tüm alanlarda tutuyor.
  **KAPI: 22/23 = %95.65** (G-013 doğrulanamayan sayıldığında); doğrulanabilirler üzerinde %100. Eşik %90 → GEÇTİ.
  Not: kâhin CSV'si gelince aynı betik onunla tekrar çalıştırılmalı; bu oran SPEC'teki tablodan türetilmiştir.
- statsmodels (`reports/statsmodels_report.md`): 594/594 a priori vektörde `n_total = ⌈N_sm⌉`; 594/594 minimallik
  (güç(n_total) ≥ hedef, güç(n_total − 1) < hedef); 300/300 post hoc güç 7 ondalıkta eşit (en büyük fark 4.4e-16).
  R `pwr` makinede kurulu olmadığı için kullanılmadı.

### Kesirli N ↔ tamsayı N ilişkisi (SPEC §4.5/4)

statsmodels ve gpower-clone aynı sürekli denklemi (güç(w, α, N) = hedef) çözer. statsmodels kökü kesirli döndürür;
gpower-clone kökü 10 ondalığa yuvarlayıp (⌊N·10¹⁰ + 0.5⌋/10¹⁰) yukarı yuvarlar ve en az 1 yapar. Güç N'de
arttığından bu, hedefe ulaşan en küçük tamsayıdır ve ⌈N_sm⌉'e eşittir. Ayrılık yalnızca kök bir tamsayıya çok
yakınsa olabilir: kesir < 5·10⁻¹¹ ise G*Power kuralı aşağı yuvarlar (104.00000000003 → 104), ayrıca iki çözücünün
toleransı farklıdır. Izgarada kesirli kökler arasındaki en büyük fark 2.5·10⁻⁶ (göreli 2.5·10⁻⁷); kökteki artık
gpower-clone'da 1.5·10⁻¹², statsmodels'te 8.5·10⁻⁸. Yani fark statsmodels çözücüsünün gevşek toleransından geliyor.
Hiçbir kök bir tamsayıya 10⁻⁶'dan yakın değildi, bu yüzden bu ızgarada kural farkı ortaya çıkmadı.

## Tasarım kararları (SPEC'te tanımlı değil)

1. **Kök bulunamadığında (G-007, güç = α).** f(N) = güç − α her N > 0 için pozitif olduğundan aralık [1, 2.21875]
   uçlarında aynı işaretlidir ve Brent "kök bulunamaz" der (§4.5/3). Ancak SPEC çıktıyı n_total = 1 olarak veriyor.
   Karar: f(alt) ≥ 0 ise N = alt (= 1) alınır; aksi hâlde hata `Unable to find a total sample size for the given
   parameters.` (bu mesaj uydurmadır, G*Power'da gözlenmedi). **Soru:** G*Power bu durumda tam olarak ne yapıyor?
2. **Brent toleransı.** "Tolerans 1e-10" mutlak x toleransı olarak yorumlandı; klasik Brent/zeroin'deki gibi
   tol1 = 2·eps·|b| + 0.5·1e-10 kullanıldı (büyük N'de, ör. G-013, mutlak 1e-10 double ile ulaşılamaz).
   300 iterasyonda yakınsamazsa kök bulunamamış sayılır. Döndürülen değer zeroin'in `b` tahminidir.
3. **Aralık genişletmede taşma.** üst sonsuza giderse hata (yukarıdaki uydurma mesajla). Pratikte erişilemez.
4. **Kritik değer** `chi2.isf(α, df)` ile hesaplanır (matematiksel olarak (1 − α) quantile'ı; küçük α'da 1 − α'nın
   yuvarlama kaybını önler). Güç SPEC §4.3'teki gibi `1 − CDF` ile hesaplanır; λ < 1e-100 için merkezi χ² CDF.
   Merkezi olmayan CDF için scipy `ncx2.cdf` kullanılır (§4.4 izin veriyor); G*Power'ın Poisson toplamı yeniden yazılmadı.
5. **Post hoc kesirli N (A-3)** reddedilir: `Total sample size must be an integer.` (uydurma mesaj). Önce aralık
   kontrolü yapılır, sonra tamsayılık (0.5 → aralık mesajı). `1e2` gibi tamsayı değerli yazımlar kabul edilir.
6. **Ayrıştırma hataları** (mesajlar uydurma, İngilizce): eksik `--test`/`--mode`/zorunlu parametre, bilinmeyen
   parametre/test/mod, sayıya çevrilemeyen ya da sonlu olmayan değer (NaN, ±∞; SPEC §2.2'deki tasarım kararı).
   Kontrol sırası: argparse (bilinmeyen parametre) → test → mod → zorunlu parametre varlığı → sayıya çevirme →
   motor doğrulaması (§2.1 sırası). Yani eksik bir parametre, var olan bir df hatasından önce raporlanır.
7. **Moda ait olmayan bilinen parametreler** (ör. a priori'de `--n`) yok sayılır.
8. **Çıkış kodları:** başarı 0, girdi/ayrıştırma hatası 1, beklenmeyen iç hata 2. Hata JSON'u stdout'a yazılır.
9. **JSON biçimi:** boşluksuz (`separators=(",", ":")`), alan sırası `n_total, actual_power, critical, df, ncp`.
   `df` ondalık olarak yazılır (`1.0`, `2.5`); `n_total` her zaman tamsayıdır (G-013'te 7848860509327).
10. **Seçenek kısaltmaları** kapalı (`allow_abbrev=False`); `--w=0.3` biçimi kabul edilir.
11. **Diferansiyel düzenek:** hata vektöründe `notes` hücresinde metin içinde çift tırnak varsa tırnak içi, yoksa
    (hücrenin tamamı CSV tırnağıyla yazılmışsa) hücrenin tamamı beklenen mesajdır. KAPI oranı muhafazakâr hesaplanır:
    bilimsel gösterimli `n_total` (A-5) tam eşleşme sayılmaz; doğrulanabilirler üzerindeki oran ayrıca verilir.
    Fixture'daki `df_out` hücreleri SPEC'te yoktur; girdi df'nin G*Power'daki olası görünümü (`1`, `2.5`) yazıldı.

## SPEC'e dair sorular / açık noktalar

- **A-1** `--w`, `--df`, `--n` adları CONTRACT.md ile doğrulanmadı; eş adlar (`--n-total`, `--n_total`, `--mode posthoc`) kabul ediliyor.
- **A-2** Sayılar tam hassasiyetle yazılıyor (yuvarlamasız double).
- **A-3** Post hoc kesirli N → hata (karar 5). G*Power davranışı bilinmiyor.
- **A-4** Kritik değer yöntemi: scipy `chi2.isf`; SPEC'teki 30 vektörün tüm `critical` değerleri ekran basamağında tuttu.
- **A-5** G-013: bizim n_total = 7848860509327; ekranda `7.8489e+12` → yalnızca 5 anlamlı basamakta doğrulandı.
  Tam değer doğrulanamaz; KAPI'de "doğrulanamayan" olarak raporlanıyor.
- **S-1** (yeni) G-007'de kök bulucunun "kök bulunamaz" durumunda G*Power ne döndürüyor? (karar 1)
- **S-2** (yeni) Ayrıştırma/eksik parametre hatalarının mesaj metni ve öncelik sırası SPEC'te yok (karar 6).
- **S-3** (yeni) Çıktıdaki `df` tamsayı mı (`1`) ondalık mı (`1.0`) yazılmalı? Sayısal olarak eşit; sözleşme belirsiz.
- **S-4** (yeni) Moda ait olmayan parametre (a priori'de `--n`) hata mı olmalı? Şu an yok sayılıyor (karar 7).

## Uyuşmazlıklar

SPEC §6'daki 30 vektörün hiçbirinde uyuşmazlık yok; statsmodels karşılaştırmasında da yok. Sayı ayarı yapılmadı.
