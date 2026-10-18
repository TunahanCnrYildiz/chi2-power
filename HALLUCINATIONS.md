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

## H-003 · Çağrıya geçirilen sabiti "tolerans" diye SPEC'e yazmak

- **Ajanın iddiası:** İnceleme oturumu, a priori fonksiyonunun kök bulucuya geçirdiği `1e-10` sabitini görünce SPEC v1.0 – v1.1 §4.5'e "Tolerans 1e-10" yazdı. Ancak kök bulucunun döngüsünde bu değerin durma koşulunda kullanıldığını doğrulamadı.
- **Defter kaydı:** `LEDGER L-018`. İlk sürüm: "kök bulucu tolerans 1e-10 … ile N'yi bulur".
- **Nasıl fark edildi:** Yazım oturumu (Oturum 2), "tolerans 1e-10" ifadesini nasıl uygulayacağını tasarım kararı olarak sordu (NOTES karar 2, soru S-1). İnceleme oturumu cevap verirken kök bulucunun kanıtına (L-020) geri döndü. Döngüdeki durma koşulunun yalnızca göreli `1.11e-16·|b|` ölçütünü kullandığı, `1e-10`'un ise döngüde okunduğunun gözlenmediği ortaya çıktı.
- **Yakalayan test:** Doğrudan bir sayı farkı yaratmadı. Kök, 10 basamaklı yuvarlamadan çok daha hassas bulunduğu için 30 oracle vektörünün ve 894 statsmodels vektörünün hepsi iki yorumla da tuttu. Hatayı yakalayan, temiz oda sürecinin kendisi oldu: yazım oturumunun SPEC'teki belirsizliği soru olarak geri göndermesi.
- **Doğrusu:** SPEC v1.2 §4.5/3: durma ölçütü göreli; `1e-10` geçirilir ama kullanımı gözlenmedi. Ayrıca kök bulunamazsa ve iterasyon dolarsa hata verilmez. LEDGER L-018 düzeltildi.
- **Ders:** Bir fonksiyona geçirilen sabit, o fonksiyonun içinde nasıl kullanıldığı görülmeden adlandırılmamalı. "Argüman" ile "davranış" ayrı kanıtlardır.
