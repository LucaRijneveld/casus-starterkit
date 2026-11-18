# Deel 2: verschil met Finance (augustus 2026, alle landen)

> Ik heb de analyse met Claude gedaan via `clean_sql` op de clean database.

## Kort gezegd

Finance rapporteert €34.615,53 en 5.086 vouchers. Mijn tool komt volgens de regels uit op €32.472,08 en 4.948 vouchers. Het verschil is **€2.143,45 en 138 vouchers**. Ik vond twee verschillen met de regels:

1. **Testpartners zijn meegeteld:** +€2.052,34 en +119 vouchers.
2. **De verwerkingsdatum is gebruikt in plaats van de aankoopdatum:** +€91,11 en +19 vouchers.

| Stap | Omzet | Vouchers |
|---|---|---|
| Juiste omzet (volgens de regels) | €32.472,08 | 4.948 |
| + testpartners meetellen | + €2.052,34 = €34.524,42 | + 119 = 5.067 |
| + verwerkingsdatum i.p.v. aankoopdatum | + €91,11 = **€34.615,53** | + 19 = **5.086** |
| Finance | €34.615,53 | 5.086 |

Mijn berekening komt zo precies overeen met Finance, tot op de cent en op het aantal vouchers.

## Stappen

1. Ik berekende eerst de juiste omzet volgens de regels uit de datasetbeschrijving: betaald, geen testpartners, aankoopdatum in Amsterdamse tijd, begin- en einddatum inclusief, en commissie.
2. Daarna zette ik de mogelijke oorzaken op een rij: testpartners, verwerkings- of aankoopdatum, status, tijdzone, einddatum, klantprijs in plaats van commissie en vermenigvuldigen met het aantal vouchers.
3. Ik testte elke oorzaak apart met `reconciliate_clean`. Geen enkele verklaarde het hele verschil.
4. Met `reconciliate_rapport` testte ik de combinaties. Die tool probeert alle 128 mogelijkheden. Alleen *testpartners + verwerkingsdatum* komt precies uit op €34.615,53.
5. Als extra controle vergeleek ik ook het aantal vouchers. Dat komt eveneens uit op 5.086.

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

## Mijn conclusie

Mijn berekening klopt volgens de regels. Finance moet testpartners weglaten en rapporteren op aankoopdatum. Ik wil dit ook voor andere maanden nagaan; misschien geldt hetzelfde daar.
