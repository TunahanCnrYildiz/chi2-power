# SPEC · χ² olumsallık tablosu güç analizi

> Bu belge Oturum 2'nin (yazım) göreceği **tek** kaynaktır.
> Decompile çıktısı, adres ya da kod alıntısı içermez; yalnızca davranış, formül ve kabul kriterleri.
> Her kuralın sonunda dayandığı defter kaydı belirtilir: `(LEDGER L-0xx)`.

Sürüm: taslak · Kaynak binary: G\*Power 3.1.9.7

## 1. Kapsam

- Test: χ² testi, olumsallık tablosu (CLI etiketi `chi2-contingency`)
- Modlar: `a-priori` (toplam N hesapla), `post-hoc` (güç hesapla)

## 2. Girdiler

_TODO — parametre adları CONTRACT.md'den._

| Parametre | Tip | Geçerli aralık | Kaynak |
|---|---|---|---|
| w | ondalık | _TODO_ | |
| alpha | ondalık | _TODO_ | |
| power | ondalık | _TODO_ (yalnızca a priori) | |
| n_total | tamsayı | _TODO_ (yalnızca post hoc) | |
| df | tamsayı | _TODO_ | |

## 3. Çıktılar

_TODO — JSON alan adları ve basamak sayıları._

## 4. Hesap kuralları

### 4.1 Merkezi olmama parametresi
_TODO_

### 4.2 Kritik değer
_TODO_

### 4.3 Güç
_TODO_

### 4.4 A priori N araması ve yuvarlama
_TODO_

### 4.5 Geçersiz girdiler
_TODO_

## 5. Kabul kriterleri

```gherkin
Feature: χ² olumsallık tablosu güç analizi

  Background:
    Given test ailesi "chi2-contingency"

  # TODO: Gerçek değerler oracle/ vektörlerinden doldurulacak. Uydurma sayı yazılmaz.

  Scenario: A priori modda gereken toplam N
    Given mod "a-priori"
    And w <w>, alpha <alpha>, power <power>, df <df>
    When hesaplama yapılır
    Then "n_total" tam olarak <n_total> olur
    And "actual_power" ilk 4 basamağa kadar <actual_power> olur

  Scenario: Post hoc modda güç
    Given mod "post-hoc"
    # TODO

  Scenario: Sınır değer — güç alpha'ya eşit ya da ondan küçük
    # TODO

  Scenario: Geçersiz girdi
    Given df 0
    When hesaplama yapılır
    Then çıktı {"error": "<açıklama>"} olur
    And çıkış kodu sıfırdan farklıdır
```
