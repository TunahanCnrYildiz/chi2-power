# Halüsinasyon Günlüğü

Ajanın kendinden emin ama yanlış çıkardığı iddialar. Hedef: en az 2 kayıt.

## H-001 · Gerçek bir formülü "decompile hatası" sanmak

- **Ajanın iddiası:** İnceleme oturumunda (Oturum 1, 2026-10-16) ajan, a priori arama aralığını kuran fonksiyonda (`0x4962d0`) daraltma adımının decompile çıktısındaki `x ← (x + 1)·0.5 − 1` ifadesini "beklenen yarılama formülüyle tutarsız" bularak bunun bir decompiler hatası olduğunu, gerçek davranışın standart yarılama `(x + 1)·0.5` olduğunu varsaydı ve kullanıcıya da bu şekilde raporladı.
- **Defter kaydı:** `LEDGER L-026` (`[AJAN]`).
- **Nasıl fark edildi:** "Bunun kanıtı hangi fonksiyonda?" ilkesiyle iddia, decompile yerine doğrudan montaj (assembly) üzerinden sınandı. `0x4963ec: ADDSD` / `0x4963f0: MULSD [0x005c29a8]` / `0x4963f8: SUBSD` dizisi ve REA `read-bytes` ile okunan sabit (`0x5c29a8` = 0.5), ifadenin decompiler'ın uydurması değil, binary'nin gerçek davranışı olduğunu gösterdi.
- **Yakalayan test:** REA montaj kontrolü (`ev_b4e96ae2…95ecbf`, `ev_5431cafb…2f1aa8`). Diferansiyel testte N < 100 olan vektörler (G-004: N = 93, G-007: N = 1, planlanan G-009/G-010) bu dalı çalıştırır.
- **Doğrusu:** `LEDGER L-028` `[REA]`: daraltma adımı gerçekten `x ← (x + a)·0.5 − a`'dır (a = 1).
- **Ders:** Decompile çıktısı "garip" göründüğünde onu düzeltmek yerine montajla doğrula. Ajan, decompiler'ın bir hatasını varsaymayı kanıt yerine koydu.

## H-002 · Evidence kimliklerinin sonunu uydurmak

- **Ajanın iddiası:** LEDGER'a `[REA]` satırları yazılırken ajan, uzun Evidence kimliklerini `ev_xxxxxxxx…yyyyyy` biçiminde elle kısalttı. Kısaltmaların bir kısmında son karakterleri gerçek kimlikten değil hafızadan "tamamladı". Örneğin aralık kurma fonksiyonunun kanıtı `ev_b4e96ae2…f4ecbf` diye yazıldı; gerçek kimlik `…95ecbf` ile bitiyor.
- **Defter kaydı:** `LEDGER L-019` ve diğer `[REA]` satırları (kanıt sütunu).
- **Nasıl fark edildi:** Ajan kısaltmaları yazdıktan sonra şüphelendi ve `re-work/` altındaki gerçek REA JSON çıktılarından kimlikleri ön ekle eşleştiren bir betik çalıştırdı. Betik birden fazla kısaltmanın gerçek kimlikle uyuşmadığını gösterdi.
- **Yakalayan test:** Evidence dizini doğrulama betiği (ön ek → tam kimlik eşlemesi; eşleşmeyen ya da birden çok eşleşen kısaltma hata sayılır). Son çalıştırmada 33 kimliğin tamamı eşleşti, çözülemeyen kimlik yok.
- **Doğrusu:** LEDGER'daki tüm kısaltmalar artık gerçek kimliklerden üretiliyor; tam kimlikler LEDGER sonundaki "Evidence dizini" tablosunda.
- **Ders:** İzlenebilirlik puanı `[REA]` satırlarına veriliyor; kanıt kimliği uydurmak, kanıtın kendisini uydurmakla aynı risktir. Kimlikler elle değil, araç çıktısından kopyalanmalı.
