# MongoDB projekat - predmet Sistemi baza podataka

**Tema:** Analiza skupa podataka 'Global Fashion Retail Sales'

**Autori:** Milica [indeks] i Saška [indeks]

## Opis skupa podataka

Podaci koji su uzeti u obzir tokom izrade projekta potiču sa sajta Kaggle. Konkretno, naziv dataset-a je 'Global Fashion Retail Analytics Dataset'. Dataset je sintetički generisan i simulira dvogodišnje maloprodajne transakcije multinacionalnog modnog brenda. Sadrži podatke ukratko o:

- 35 prodavnica u 7 zemalja (SAD, Kina, Nemačka, UK, Francuska, Španija, Portugal)
- 1.6+ miliona kupaca
- Preko 6.4 miliona transakcija (kupovine i povrati)
- ~2.000 proizvoda, sa opisima na 6 jezika
- ~200 zaposlenih
- ~50 promotivnih kampanja (popusti)

Sve zajedno podaci su raspoređeni na 6 kolekcija dokumenata.

## Upiti

1. Za svaki mesec pronaći zemlju sa najvećim prihodom i unutar nje prodavnicu koja je najviše doprinela.
2. Za svaku kategoriju i zemlju odrediti prosečnu maržu i koji mesec u godini generiše najveći prihod.
3. Za transakcije veće od 200, pronaći kupce koji su kupovali u više od jedne zemlje, u kojim zemljama kupuju i koliko troše po zemlji.
4. Za svaku boju odrediti u kom kvartalu se najviše prodaje.
5. Pronaći 10 kupaca sa najvećim ukupnim popustom (unit_price × quantity × discount) — ko je najviše iskoristio popuste.
6. Za svaku prodavnicu odrediti koji meseci u prvoj i drugoj godini imaju najveći i najmanji prihod, i koji je mesečni prosek između godina.
7. Za svaki proizvod koji je vraćan, odrediti stopu povrata i prosečnu cenu po kojoj je kupljen.
8. Za svaki sat u danu odrediti koji payment method dominira i koliki prihod generiše, i u kojoj prodavnici taj payment method u tom satu ostvaruje najveći prihod.
9. Za svakog zaposlenog odrediti u kom mesecu je ostvario najveći prihod i koliko je to odstupalo od njegovog godišnjeg proseka.
10. Za top 5 kupaca odrediti omiljenu prodavnicu, omiljenu kategoriju, omiljenu boju i prosečan iznos transakcije.

## Implementacija

Implementacioni deo projekta (skripta za uvoz podataka) se nalazi u glavnom direktorijumu:
- `uvoz_podataka.py` — uvoz transakcija sa spajanjem customers/products/stores/employees, i uvoz discounts kampanja

Detaljan kod i rezultati svakog upita nalaze se u pripadajućim direktorijumima:

| Autor | Direktorijum |
|---|---|
| Milica | [milica/](./milica) |
| Saška | [saska/](./saska) |

## Statistika i grafici

_[Ovde ide grafik broja pregledanih dokumenata pre/posle indeksiranja, i grafik vremena trajanja upita pre/posle — videti performanse_template.xlsx]_

![Broj dokumenata - pre i posle](./grafici/broj_dokumenata.png)

![Vreme izvršavanja - pre i posle](./grafici/vreme_izvrsavanja.png)

---

## Inicijalna šema baze podataka

### Kolekcije i polja

Pregled izvornih podataka (CSV fajlovi) i njihovih polja, pre prebacivanja u MongoDB.

#### CUSTOMERS

```
• customerId – jedinstveni numerički identifikator kupca
• name – puno ime (može sadržati titule)
• email – anonimizovani email
• telephone – broj telefona
• city – grad stanovanja
• country – država stanovanja
• gender – pol (F, M, D)
• dateOfBirth – datum rođenja
• jobTitle – zanimanje (opciono)
```

#### PRODUCTS

```
• productId – jedinstveni numerički identifikator proizvoda
• category – visoka klasifikacija (Feminine, Masculine, Children)
• subCategory – specifičnija klasifikacija
• descriptionPt, descriptionDe, descriptionFr, descriptionEs, descriptionEn, descriptionZh – opisi na 6 jezika
• color – boja proizvoda
• sizes – dostupne veličine
• productionCost – trošak proizvodnje u USD
```

#### STORES

```
• storeId – jedinstveni identifikator prodavnice
• country – država
• city – grad
• storeName – naziv u formatu Store [Grad]
• numberOfEmployees – broj zaposlenih
• zipCode – poštanski broj
• latitude – geo. širina
• longitude – geo. dužina
```

#### EMPLOYEES

```
• employeeId – jedinstveni identifikator zaposlenog
• storeId – referenca ka odgovarajućoj prodavnici
• name – puno ime
• position – uloga u prodavnici (npr. Store Manager, Sales Associate)
```

#### DISCOUNTS

```
• startDate – datum početka kampanje
• endDate – datum kraja kampanje
• discount – decimalna vrednost popusta
• description – opis kampanje
• category – kategorija na koju se odnosi
• subCategory – podkategorija na koju se odnosi
```

> Napomena: discounts.csv nema jedinstveni identifikator — veza sa transakcijama je po vrednosti popusta i datumu, ne po FK.

#### TRANSACTIONS

```
• invoiceId – identifikaciona oznaka fakture (format: INV-/RET- + kod države + ID prodavnice + redni broj)
• line – redni broj stavke unutar fakture
• customerId – referenca ka odgovarajućem kupcu
• productId – referenca ka odgovarajućem proizvodu
• size – veličina varijante
• color – boja varijante
• unitPrice – cena jedinice pre popusta
• quantity – broj kupljenih jedinica
• date – datum i vreme transakcije
• discount – primenjeni popust (decimalno)
• lineTotal – ukupno za stavku nakon popusta
• storeId – referenca ka odgovarajućoj prodavnici
• employeeId – referenca ka odgovarajućem zaposlenom
• currency – ISO kod valute
• currencySymbol – simbol valute
• sku – inventarni kod
• transactionType – Sale ili Return
• paymentMethod – način plaćanja
• invoiceTotal – ukupna vrednost cele fakture
```

### Odnosi između kolekcija (izvorni FK)

```
TRANSACTIONS.customerId   ->  CUSTOMERS.customerId
TRANSACTIONS.productId    ->  PRODUCTS.productId
TRANSACTIONS.storeId      ->  STORES.storeId
TRANSACTIONS.employeeId   ->  EMPLOYEES.employeeId
EMPLOYEES.storeId         ->  STORES.storeId
```

`DISCOUNTS` nema formalnu FK vezu — povezuje se sa transakcijama posredno, preko vrednosti popusta i vremenskog perioda važenja kampanje.

### Logički model u MongoDB (ugnježdeni dokument)

Pošto se podaci o kupcu, proizvodu, prodavnici i zaposlenom uvek čitaju zajedno sa transakcijom i ne menjaju se retroaktivno, odabran je **embedded model** — svi povezani podaci se ugnježdavaju direktno u dokument `transactions`, umesto da se referenciraju (izbegava se potreba za `$lookup` pri osnovnim upitima).

`discounts` ostaje kao zasebna kolekcija jer nema FK vezu sa transakcijama.

```json
{
  "invoice_id": "INV-DE-007-00001",
  "line": 1,
  "date": "2023-11-15T14:23:00Z",
  "transaction_type": "Sale",
  "payment_method": "Credit Card",
  "unit_price": 198.00,
  "quantity": 1,
  "discount": 0.15,
  "line_total": 168.30,
  "invoice_total": 168.30,
  "currency": "EUR",
  "currency_symbol": "€",
  "sku": "FESH441-M-BLACK",
  "size": "M",
  "color": "BLACK",
  "customer": {
    "customer_id": 8821,
    "name": "Ana Müller",
    "email": "ana.muller@fake_gmail.com",
    "city": "Berlin",
    "country": "Germany",
    "gender": "F",
    "date_of_birth": "1994-05-12"
  },
  "product": {
    "product_id": 441,
    "category": "Feminine",
    "sub_category": "Coats and Blazers",
    "production_cost": 34.20
  },
  "store": {
    "store_id": 7,
    "store_name": "Store Berlin",
    "country": "Germany",
    "city": "Berlin"
  },
  "employee": {
    "employee_id": 112,
    "name": "Jonas Weber",
    "position": "Sales Associate",
    "store_id": 7
  }
}
```

### Kolekcija DISCOUNTS (zasebna, bez ugnježdavanja)

```json
{
  "start_date": "2023-11-01",
  "end_date": "2023-11-30",
  "discount": 0.15,
  "description": "Black Friday",
  "category": "Feminine",
  "sub_category": "Coats and Blazers"
}
```
