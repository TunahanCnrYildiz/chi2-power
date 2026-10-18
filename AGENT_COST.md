# Ajan Maliyet ve Süreç Günlüğü

## Hangi ajan?

- **Ajan:** Claude Code (Claude masaüstü uygulaması, Code sekmesi). Model **Claude Opus 5.5** (`claude-opus-5-5`); iki oturumdaki bütün çağrılar bu modelle yapıldı.
- **İnceleme araçları:** REA (`rea-agents` 6.5.0) ve Ghidra 12.1.4 sağlayıcısı.
- **Abonelik:** Claude Pro. Çalışma abonelik kapsamında yapıldı, ayrıca API ücreti ödenmedi. Aşağıdaki dolar tutarları, aynı kullanımın API fiyatlarıyla ne kadar tutacağını gösteren tahminlerdir.

## Token ve maliyet

Token sayıları her oturumun Claude Code kayıt dosyasındaki (`~/.claude/projects/…/*.jsonl`) `usage` alanlarından toplandı. Aynı mesaj kimliği bir kez sayıldı. Durum 18 Ekim 2026 itibarıyladır. Bütün oturumlar Claude Opus 5.5 ile çalıştı.

| | Oturum 1 · inceleme | Oturum 2 · yazım | GUI yolu (1. deneme) | GUI yolu (ölçüm) | Toplam |
|---|---|---|---|---|---|
| Kullanıcı / üst oturum mesajı | 43 | 8 | 1 | 1 | 53 |
| Model çağrısı | 287 | 169 | 8 | 31 | 495 |
| Araç çağrısı | 389 | 196 | 8 | 34 | 627 |
| Önbelleğe yazılan girdi token | 1 034 065 | 348 457 | 58 772 | 111 836 | 1 553 130 |
| Önbellekten okunan girdi token | 96 614 805 | 40 299 955 | 660 951 | 3 620 256 | 141 195 967 |
| Çıktı token | 282 140 | 194 787 | 2 157 | 14 218 | 493 302 |
| **API eşdeğeri maliyet (tahmin)** | **≈ 30 – 33 $** | **≈ 14 – 15 $** | **≈ 0.5 $** | **≈ 1.6 – 1.9 $** | **≈ 46 – 50 $** |

Önbelleksiz girdi her oturumda birkaç yüz token düzeyinde olduğu için tabloya alınmadı.

**Ajanın kendi çalıştırmaları.** Ajan katmanının değerlendirmesi ayrıca 140 `claude -p` çağrısı yaptı. Bunlar yukarıdaki oturumların dışındadır:

| Çalıştırma | Çağrı | Token |
|---|---|---|
| Ana ajan, Opus 5.5 (ana sonuç) | 10 | 50 811 |
| Ana ajan, Opus 4.8 (eski CLI'deki ilk çalıştırma) | 10 | 47 126 |
| Sistem 1, Haiku 5.5 (ana sonuç) | 60 | 109 482 |
| Sistem 1, Haiku 4.5 (ilk çalıştırma) | 60 | 175 959 |

Bu çağrıların toplam maliyeti birkaç dolar mertebesindedir; ayrıntılar `tests/reports/agent_report.md` dosyasında.

**Maliyet hesabı.** Opus 5.5 liste fiyatları (1M token başına):

| Kalem | Fiyat | Not |
|---|---|---|
| Girdi | 4 $ | |
| Çıktı | 20 $ | |
| Önbellekten okuma | 0.20 $ | |
| Önbelleğe yazma | 5 $ – 8 $ | 5 dakikalık önbellek ≈ girdi × 1.25; 1 saatlik ≈ × 2. Hangi sürenin kullanıldığı kayıtta ayrışmadığı için aralık verildi. |

Çalışma Pro abonelik kapsamında yapıldı; ayrıca API ücreti ödenmedi.

**Maliyetin dağılımı.**
- Girdinin %98'den fazlası önbellekten okundu; her model çağrısı konuşma geçmişini yeniden gönderir.
- İnceleme oturumunda maliyetin yarıdan fazlası bu okumalardan geliyor. Oturum uzadıkça her çağrı daha pahalı hâle geldi.

**REA / Ghidra.** REA çağrıları model token'ı harcamaz, yerel bilgisayarda çalışır. Toplam 37 REA CLI çalıştırması yapıldı:

| Komut | Adet |
|---|---|
| `function` | 22 |
| `read-bytes` | 7 |
| `trace` | 4 |
| `search` | 2 |
| `xrefs` | 1 |
| `analyze` | 1 |

Her çalıştırma Ghidra analizini baştan yaptığı için ~90 saniye sürdü; çoğu 4–6'lı gruplar hâlinde paralel çalıştırıldı. Bunlara birkaç MCP çağrısı da eklendi (`binary_session`, `inspect_pe_resources`, `open_binary`).

## Kaç iterasyon?

### Oturum 1 · inceleme

| Aşama | Ne oldu |
|---|---|
| Kurulum | REA'nın Ghidra'yı görmesi 4 deneme sürdü: kullanıcı ortam değişkeni → sistem değişkeni → `~/.claude.json` kaydı → masaüstü uygulamasının MSIX kaydı. Asıl sorun, uygulamanın MCP sunucularına ortam değişkenlerini aktarmaması çıktı. |
| Sözleşme | Yönergedeki `CONTRACT.md` bağlantısının boş olduğu 3 adımda anlaşıldı. |
| REA ile inceleme | 8 tur. Her tur ~2 dakikalık paralel bir REA grubuydu. Zincir: dizeler → doğrulama fonksiyonları → mod yönlendiricisi → vtable / RTTI → a priori ve post hoc → λ, yuvarlama, kök bulucu → aralık kurma montajı → hedef fonksiyon. |
| Kâhin | 8 + 22 vektör (kullanıcı topladı, ajan okuyup CSV'ye işledi). |
| SPEC | 4 sürüm: v1.0 → v1.1 (30 vektör ve kılavuz) → CLI adlarının kaynağı → v1.2 (yazım oturumunun soruları). |

### Oturum 2 · yazım

3 tur:
1. İlk tur: kabul testleri (kırmızı) → motor ve CLI (yeşil) → diferansiyel düzenek → NOTES.
2. SPEC v1.2 düzeltmeleri: yine önce kırmızı testler, sonra yeşil kod.
3. MCP sunucusu (bonus): kırmızı testler → ortak katman `service.py` ve `mcp_server.py` (yeşil) → NOTES.
4. AI ajanı (bonus): rows/cols → df motorda; Sistem 1 ve MCP ajanı; değerlendirme ve MCP ↔ GUI karşılaştırması.
   - Gerçek çalıştırmalar iki kez engellendi: önce `claude` CLI'de giriş yoktu, sonra eski CLI Opus 5.5'i desteklemiyordu. Kullanıcı girişi yaptı ve CLI'yi güncelletti.
   - Ölçüm, GUI yoluyla aynı model olsun diye Opus 5.5 ile tekrarlandı. Prompt ve puanlama tekrarda değiştirilmedi.

Hiçbir turda bir vektör için sayı ayarı yapılmadı.

### GUI yolu

İki oturum:
1. İlk oturumda bilgisayar kullanımı araçları yoktu: ayar, oturum açıldıktan sonra açılmıştı ve araçlar ancak oturum başlarken yükleniyor. Bu oturum hiçbir soruyu çözmedi.
2. İkinci oturum 10 soruyu ~130 saniyede, 16 ekran görüntüsüyle çözdü.

### Ajan hataları

3 kayıt, ayrıntıları [`HALLUCINATIONS.md`](HALLUCINATIONS.md) dosyasında. Bunlara ek olarak inceleme oturumu bazı mesajları Türkçe yerine İngilizce yazdı ve kullanıcının uyarısıyla düzeltti.

## Neyi farklı yapardım?

1. **Ghidra'yı MCP kaydına baştan bağlardım.** `GHIDRA_INSTALL_DIR` doğrudan masaüstü uygulamasının REA kaydının `env` alanına yazılsaydı, kurulumdaki 4 deneme ve 3 uygulama yeniden başlatması olmazdı.
2. **İlk analizi en başta kalıcı bir veritabanına kaydederdim.** MCP zaman aşımı yüzünden her CLI çağrısı Ghidra analizini baştan yaptı (37 × ~90 sn ≈ 55 dakika). Analizi bir kez yapıp kalıcı bir Ghidra projesinde tutmak ya da MCP zaman aşımını artırmak bu süreyi büyük ölçüde azaltırdı.
3. **Evidence kimliklerini hiçbir zaman elle yazmazdım.** LEDGER'ı baştan REA çıktılarından üreten bir betikle yazmak H-002'yi önlerdi.
4. **"Argüman" ile "davranış"ı ayırırdım.** Bir fonksiyona geçirilen sabiti (1e-10), fonksiyonun içinde nasıl kullanıldığını görmeden "tolerans" diye SPEC'e yazmazdım (H-003). Garip görünen decompile çıktısını da hata saymadan önce montajla doğrulardım (H-001).
5. **Oracle vektörlerini SPEC'ten önce toplatırdım.** 30 vektör geldikten sonra 4 ayrıntı düzeltildi: hata mesajlarının tam metni, kesirli df, ekrandaki değişken basamak sayısı ve G-013'teki dev N. Vektörler daha erken gelse SPEC v1.0 daha az revizyon gerektirirdi.
6. **Hocaya sözleşmeyi ilk gün sorardım.** χ²'ye özgü parametre adları hâlâ çıkarım. Classroom'a ilk gün yazılacak bir soru bu belirsizliği erkenden kapatırdı.
7. **Ölçüm ortamını en başta doğrulardım.** Ajan ölçümünden önce şunları kontrol etmek, iki gereksiz turu ve bir yeniden ölçümü önlerdi:
   - `claude` CLI'de giriş var mı (`claude auth status`)?
   - CLI sürümü hedef modeli destekliyor mu?
   - Model, takma ad yerine açık kimlikle (`claude-opus-5-5`) mi verildi?
   - Bilgisayar kullanımı oturum açılmadan önce açık mı?
8. **İnceleme oturumunu daha kısa tutardım.** Maliyetin büyük kısmı, uzayan oturumun geçmişini her çağrıda yeniden okumaktan geldi. Kurulum, inceleme ve SPEC yazımı ayrı oturumlara bölünseydi (her biri kısa bir devir notuyla) token kullanımı belirgin şekilde düşerdi.

## Süreç notları

- **2026-10-16:**
  - Yönerge okundu, G\*Power 3.1.9.7 resmi sayfadan indirildi ve hash'ler alındı, repo iskeleti kuruldu.
  - REA + Ghidra kurulumu tamamlandı; inceleme yapıldı ve LEDGER'a 22 `[REA]` kaydı girdi.
  - 30 oracle vektörü toplandı, kılavuzdan 4 `[DOK]` kaydı eklendi, SPEC v1.1 yazıldı.
- **2026-10-18:**
  - Oturum 2 temiz klasörde yalnızca SPEC ile başladı; motor, CLI ve testleri yazdı.
  - Yazım oturumunun 4 sorusu SPEC v1.2'de yanıtlandı ve koda uygulandı; kod ana repoya geçmişiyle birleştirildi.
  - Sonuç: 94/94 test geçti, kâhinde 30/30 vektör tuttu, KAPI %93.33.
  - MCP sunucusu (bonus) yazım oturumunda eklendi ve birleştirildi: 128/128 test geçti, 30 vektörde CLI ile birebir aynı çıktı.
  - AI ajanı (bonus) eklendi ve ölçüldü (Opus 5.5 / Haiku 5.5): doğru seçim 10/10, Sistem 1 TR 30/30, EN 30/30. MCP ↔ GUI: 50 811 token'a karşı 2 978 621 token (hazırlık dahil 3 746 372). 187/187 test geçti.
