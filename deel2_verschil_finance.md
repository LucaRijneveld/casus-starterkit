# Deel 2: verschil met Finance (augustus 2026, alle landen)

> De analyse is met Claude uitgevoerd via `clean_sql` op de clean database.

## Kort gezegd

Finance rapporteert €34.615,53 en 5.086 vouchers. Volgens de regels komt de tool uit op €32.472,08 en 4.948 vouchers. Het verschil is **€2.143,45 en 138 vouchers**, veroorzaakt door twee afwijkingen van de regels:

1. **Testpartners zijn meegeteld:** +€2.052,34 en +119 vouchers.
2. **De verwerkingsdatum is gebruikt in plaats van de aankoopdatum:** +€91,11 en +19 vouchers.

| Stap | Omzet | Vouchers |
|---|---|---|
| Juiste omzet (volgens de regels) | €32.472,08 | 4.948 |
| + testpartners meetellen | + €2.052,34 = €34.524,42 | + 119 = 5.067 |
| + verwerkingsdatum i.p.v. aankoopdatum | + €91,11 = **€34.615,53** | + 19 = **5.086** |
| Finance | €34.615,53 | 5.086 |

Zo komt de berekening precies overeen met Finance, tot op de cent en op het aantal vouchers.

## Stappen

1. Als uitgangspunt diende de omzet volgens de datasetbeschrijving: betaalde verkopen, geen testpartners, aankoopdatum in Amsterdamse tijd, inclusieve begin- en einddatum, en commissie.
2. Mogelijke oorzaken waren testpartners, verwerkings- of aankoopdatum, status, tijdzone, einddatum, klantprijs in plaats van commissie en vermenigvuldigen met het aantal vouchers.
3. Geen van deze oorzaken verklaarde het hele verschil toen ze afzonderlijk met `reconciliate_clean` werden getest.
4. `reconciliate_rapport` testte alle 128 combinaties. Alleen *testpartners + verwerkingsdatum* komt precies uit op €34.615,53.
5. Het aantal vouchers diende als extra controle en kwam eveneens uit op 5.086.

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

De berekening volgt de afgesproken regels. Finance moet testpartners weglaten en rapporteren op aankoopdatum. Een volgende stap is nagaan of dit ook voor andere maanden geldt.
