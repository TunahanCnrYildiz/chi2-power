# Oturum 2 · Yazım — ilk prompt

- Ajan: Claude Code (Opus 5.5)
- Tarih: 2026-10-18
- Çalışma klasörü: `D:\Claude Projects\Teardown Sprint - Yazim`. Ayrı bir klasör ve ayrı bir git deposu; başlangıçta yalnızca `SPEC.md` ve `.gitignore` içerir.
- Temiz oda önlemleri:
  - Bu oturum inceleme oturumunun klasörünü, kanıt defterini, ham REA/Ghidra çıktılarını ve git geçmişini görmez.
  - Claude Code'un proje hafızası klasör yoluna bağlıdır; inceleme oturumunun notları bu oturuma taşınmaz.
  - `SPEC.md`, inceleme deposundaki sürümle aynıdır (SHA-256 `58296804…0b8153b`).

Oturumu başlatan prompt aşağıdadır (birebir):

---

Sen temiz oda yöntemiyle çalışan bir **yazım** oturumusun. Bu klasördeki tek davranış kaynağın `SPEC.md`. Görevin, SPEC'te tanımlanan güç analizini (χ² testi, olumsallık tablosu; a priori ve post hoc) hesaplayan bir motor ve onu çağıran bir komut satırı aracı (CLI) yazmak.

**Temiz oda kuralları (kesin):**
- Yalnızca bu klasörde çalış. Bu klasörün dışındaki hiçbir dosyayı açma, listeleme ya da arama. Özellikle `D:\Claude Projects\Teardown Sprint` klasörüne girme.
- Tersine mühendislik araçları kullanma: REA (`mcp__rea__*` araçları ve `rea` komutu), Ghidra, disassembler veya decompiler yok. Hedef programın ikili dosyasını açma ya da çalıştırma.
- SPEC'te olmayan bir davranış gerekirse **uydurma**. Soruyu yaz, yaptığın varsayımı açıkça "tasarım kararı" olarak işaretle ve raporla.

**Dil ve araçlar:** Python 3 (makinede 3.14 kurulu). Dağılım fonksiyonları için scipy kullanabilirsin. Puanı getiren kısımlar SPEC §4.5'teki N araması, yuvarlama ve aralık kurma; bunları SPEC'te yazdığı gibi kendin uygula. Bağımlılıkları `pyproject.toml` dosyasında belirt.

**Çalışma sırası (önce test):**
1. SPEC §6'daki Gherkin kabul kriterlerini **önce test olarak** yaz (pytest). Tablolardaki her vektör ayrı bir test olsun. Testler kırmızıyken motoru yazmaya başla.
2. Motoru yaz: `src/` altında, hesap mantığının tek yeri.
3. CLI'yi motorun üstünde **ince bir katman** olarak yaz. Argümanları ayrıştırır, motoru çağırır ve JSON basar; hesap mantığı içermez.
4. Tüm testleri yeşile getir. Tutmayan bir vektör olursa SPEC'e uymak için "sayı ayarı" yapma; farkı ve olası nedenini raporla.

**CLI sözleşmesi** (SPEC §2 – §3 ile birlikte):
- Komut adı `gpower-clone` olmalı; `pyproject.toml` içinde console script olarak kur. Ayrıca `python -m` ile de çalışabilsin.
- Örnek çağrılar:
  - `gpower-clone --test chi2-contingency --mode a-priori --w 0.3 --alpha 0.05 --power 0.95 --df 1`
  - `gpower-clone --test chi2-contingency --mode post-hoc --w 0.3 --alpha 0.05 --n 100 --df 1`
- Başarılı çıktı: tek satır JSON. Alanlar `n_total`, `actual_power`, `critical`, `df`, `ncp`. Sayılar tam hassasiyetle (yuvarlamadan) yazılır; `n_total` tamsayıdır.
- Hata çıktısı: tek satır `{"error":"<açıklama>"}` ve sıfırdan farklı çıkış kodu. Açıklama SPEC §2.2'deki mesajla birebir aynı olmalı.
- SPEC §2'deki eş adları da kabul et.

**Diferansiyel test düzeneği** (`tests/` altında):
- `oracle/vectors.csv` biçiminde bir CSV okuyan ve her satır için CLI'yi gerçekten çalıştırıp sonucu karşılaştıran bir betik yaz. CSV henüz bu klasörde yok; sonradan eklenecek. Sütunlar:
  `id,source,mode,w,alpha,power,n_total_in,df,ncp,critical,df_out,n_total,actual_power,screenshot,notes`
  - Boş hücre, o alanın beklenmediği anlamına gelir.
  - Sayısal hücreler G\*Power ekranındaki metindir. Karşılaştırma, o metindeki ondalık basamak sayısına yuvarlanarak yapılır (SPEC §3).
  - Hesap sütunları boş olan bir satır bir hata vektörüdür. Beklenen mesaj `notes` sütununda çift tırnak içinde verilir.
- Betik bir uyum raporu üretsin: toplam vektör sayısı, N tam eşleşme oranı (KAPI ölçütü: en az %90), alan bazında eşleşme ve tutmayan her vektör için beklenen/bulunan değerler.
- Ek olarak R `pwr` ya da Python `statsmodels` ile **500'den fazla** vektör üreten bir betik yaz (`statsmodels.stats.power.GofChisquarePower` uygun olabilir; varlığını kendin doğrula). Bu kütüphaneler N'yi kesirli verir. Raporda kütüphanenin kesirli N'si ile bizim tamsayı N'imiz arasındaki ilişkiyi SPEC §4.5'teki yuvarlama kuralına dayanarak açıkla.
- SPEC §5'teki açık noktaları (ör. A-5) raporda ayrıca belirt.

**Teslim edeceklerin** (bu klasörde):
- `src/` (motor + CLI), `tests/` (kabul testleri, diferansiyel test betiği, statsmodels/pwr betiği), `pyproject.toml`.
- Kısa bir `NOTES.md`: kurulum ve çalıştırma komutları, verdiğin tasarım kararları, SPEC'e dair soruların, uyuşmazlıklar.
- Her anlamlı adımda git commit. Commit mesajları Türkçe olsun.

**İletişim:** Kullanıcıyla Türkçe konuş. Bittiğinde test sonuçlarını, KAPI oranını ve açık soruları özetle.
