# statsmodels karşılaştırma raporu

- Kütüphane: `statsmodels.stats.power.GofChisquarePower` (n_bins = df + 1)
- Toplam vektör: **894** (594 a priori, 300 post hoc)

## A priori: kesirli N (statsmodels) ↔ tamsayı N (gpower-clone)

- `n_total == ⌈N_sm⌉`: **594/594**
- Tamsayıya 1e-6'dan yakın N_sm (yuvarlama kuralıyla açıklanan sınır durumları): 0
- Açıklanamayan uyuşmazlık: 0
- Bizim kesirli N ile N_sm arasındaki en büyük fark: 2.496e-06 (göreli 2.450e-07)
- Kökte artık |güç(N) − hedef| en büyük değeri: gpower-clone 1.545e-12, statsmodels 8.525e-08 (fark statsmodels çözücüsünün daha gevşek toleransından)
- Minimallik (statsmodels gücüyle): güç(n_total) ≥ hedef ve güç(n_total − 1) < hedef: **594/594**
- `actual_power` ile statsmodels gücü (aynı n_total'da) en büyük mutlak fark: 5.551e-16

### İlişkinin açıklaması (SPEC §4.5/4)

İki uygulama aynı denklemi, güç(w, α, N) = hedef güç, N'yi sürekli kabul ederek çözer; statsmodels kökü kesirli olarak döndürür (ör. 144.2…). gpower-clone kökü önce 10 ondalık basamağa yuvarlar (N′ = ⌊N·10¹⁰ + 0.5⌋ / 10¹⁰), sonra yukarı yuvarlar (n_total = ⌈N′⌉) ve en az 1 yapar. Güç N'de artan olduğundan ⌈N⌉, gücü hedefe ulaştıran en küçük tamsayıdır; bu yüzden n_total = ⌈N_sm⌉ beklenir. Fark ancak kesirli kök bir tamsayıya çok yakınsa (kesir < 5·10⁻¹¹ ise G*Power kuralı aşağı yuvarlar; ayrıca iki çözücünün toleransları farklıdır) ortaya çıkabilir. Bu ızgarada böyle bir durumun sayısı yukarıda verilmiştir.

## Post hoc: güç

- 7 ondalıkta eşleşme: **300/300**
- En büyük mutlak fark: 4.441e-16
- Not: statsmodels `ncx2.sf` kullanır; gpower-clone SPEC §4.3'teki gibi `1 − CDF` kullanır. Fark makine hassasiyeti mertebesindedir.

