# Starterkit – Casus AI Engineer, Social Deal

**Begin bij `OPDRACHT.html`** (open in je browser; `OPDRACHT.pdf` is dezelfde tekst om te printen): daarin staat de volledige opdracht, wat je inlevert en hoe het gesprek daarna gaat. Dit bestand is een korte naslag bij de dataset.

**Let op:** de dataset, tabellen en regels zijn speciaal voor deze casus verzonnen. Ze bevatten geen echte gegevens van Social Deal en zijn geen kopie van onze echte database.

## Inhoud

- `OPDRACHT.html` – de opdracht (open in je browser).
- `OPDRACHT.pdf` – dezelfde opdracht om te printen.
- `socialdeal_casus.sqlite` – verzonnen dataset (SQLite, ~13 MB), gemaakt met een random generator.
- `LEESMIJ.md` – dit bestand, met de beschrijving van de dataset hieronder.

Snel bekijken: `sqlite3 socialdeal_casus.sqlite ".tables"` of open het bestand in DB Browser for SQLite / DBeaver.

## Beschrijving van de dataset

| Tabel | Rijen | Kolommen |
| --- | --- | --- |
| `steden` | 34 | `id`, `naam`, `land` (NL/BE), `regio` |
| `partners` | 613 | `id`, `naam`, `stad_id`, `is_test` |
| `deals` | 2.444 | `id`, `partner_id`, `titel`, `start_datum`, `eind_datum`, `prijs_cent`, `commissie_pct` |
| `verkopen` | 96.947 | `id`, `deal_id`, `aangemaakt_op`, `verwerkt_op`, `status`, `aantal`, `klantprijs_cent`, `commissie_cent`, `klant_email`, `betaalreferentie` |

Koppeling (er zijn geen foreign keys gedefinieerd):
`verkopen.deal_id → deals.id → deals.partner_id → partners.id → partners.stad_id → steden.id`

### Regels voor deze casus

- **Omzet = commissie**: de som van `commissie_cent`. `klantprijs_cent` (wat de klant betaalt) is géén omzet.
- Alleen status *betaald* telt mee; *geannuleerd* en *terugbetaald* niet.
- Een verkoop hoort bij de periode van `aangemaakt_op` (moment van kopen), niet van `verwerkt_op`.
- Finance rekent in Nederlandse tijd (Europe/Amsterdam), periodes van begindatum tot en met einddatum.
- Eén regel kan meerdere vouchers bevatten (`aantal`); `klantprijs_cent` en `commissie_cent` zijn al het regeltotaal.
- Een verkoop hoort bij de stad van de partner.
- Testpartners (`is_test = 1`) tellen nooit mee.
- Bedragen staan in centen (gehele getallen).

Net als echte data is deze data niet overal netjes. Welke problemen erin zitten, zoek je zelf uit.

### Persoonsgegevens

`klant_email` en `betaalreferentie` zijn persoonsgegevens: nooit in tool-uitvoer, foutmeldingen of logs.
