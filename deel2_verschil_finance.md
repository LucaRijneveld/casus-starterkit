# Deel 2: verschil met Finance (augustus 2026, alle landen)

> De analyse is uitgevoerd met Claude via de read-only SQL-tool `clean_sql` op de clean database.

## Kort

Finance rapporteert €34.615,53 en 5.086 vouchers. Onze tool geeft €32.472,08 en 4.948 vouchers. Het verschil is **€2.143,45 en 138 vouchers**. Finance telt twee dingen anders dan de regels:

1. **Testpartners zijn meegeteld:** +€2.052,34 en +119 vouchers.
2. **De verwerkingsdatum is gebruikt in plaats van de aankoopdatum:** +€91,11 en +19 vouchers.

| Stap | Omzet | Vouchers |
|---|---|---|
| Juiste omzet (volgens de regels) | €32.472,08 | 4.948 |
| + testpartners meetellen | + €2.052,34 = €34.524,42 | + 119 = 5.067 |
| + verwerkingsdatum i.p.v. aankoopdatum | + €91,11 = **€34.615,53** | + 19 = **5.086** |
| Finance | €34.615,53 | 5.086 |

Dit komt op de cent en op het aantal vouchers precies overeen met Finance.

## Stappen

1. **Juiste getal berekend** met de regels uit de dataset-beschrijving (betaald, geen testpartners, aankoopdatum in Amsterdamse tijd, begin en einde inclusief, commissie).
2. **Verdachten opgesteld:** testpartners, verwerkings- of aankoopdatum, status, tijdzone, einddatum, klantprijs in plaats van commissie, vermenigvuldigen met het aantal vouchers.
3. **Elke verdachte los getest** met `reconciliate_clean`. Geen enkele verklaart het hele verschil.
4. **Combinaties getest** met `reconciliate_rapport`, dat alle 128 combinaties probeert. Alleen *testpartners + verwerkingsdatum* geeft precies €34.615,53.
5. **Vouchers als tweede controle**, zodat het geen toeval is. Die komen ook uit op 5.086.

```sql
-- 1. Juiste getal
SELECT SUM(commissie_cent), SUM(aantal)
FROM omzet_verkopen
WHERE date(aangemaakt_op_nl) BETWEEN '2026-08-01' AND '2026-08-31';
-- 3.247.208 cent, 4.948 vouchers

-- 2. Wat Finance waarschijnlijk deed: betaald, mét testpartners, verwerkingsdatum
SELECT SUM(commissie_cent), SUM(aantal)
FROM clean_verkopen
WHERE status_clean = 'betaald'
  AND date(verwerkt_op_nl) BETWEEN '2026-08-01' AND '2026-08-31';
-- 3.461.553 cent, 5.086 vouchers
```

Hoeveel elke oorzaak apart oplevert, hangt iets af van de volgorde. Het totale verschil blijft €2.143,45.

## Conclusie

Ons getal klopt volgens de regels. Finance moet testpartners weglaten en rapporteren op aankoopdatum. Het is slim om dit ook voor andere maanden na te gaan. Het patroon geldt mogelijk niet alleen voor augustus.
