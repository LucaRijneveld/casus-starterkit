# Deel 3: testverslag, Claude met de MCP-tools

## Opzet

- De vijf vragen zijn gesteld aan Claude met de MCP-server van de starterkit gekoppeld. Claude had alle tools (onder andere `omzet_per_stad`, `omzet_per_maand`, `top_partners`, `clean_sql`), dus niet alleen `omzet_per_stad`.
- De vragen noemen geen periode. Claude gebruikte de hele dataset (oktober 2024 t/m september 2026).
- Elk antwoord is gecontroleerd met een eigen SQL-query op de clean database.

## De vijf vragen

| # | Vraag | Wat Claude deed | Klopte het? |
|---|---|---|---|
| 1 | "Totale winst" | Zei dat winst niet kan, want er zijn geen kosten in de data. Gaf in plaats daarvan de totale commissieomzet: **€973.868,69** (82.370 verkopen). | Ja |
| 2 | "Gemiddelde uitgave van een gebruiker" | Gebruikte de **klantprijs** (niet de commissie): **€74,88 per klant** (78.406 klanten), €71,28 per aankoop, €45,82 per voucher. Gebruikte `klant_id` alleen als telling. | Ja |
| 3 | "Opbrengst voor partners, top 5" | Zag dat "opbrengst" twee dingen kan betekenen en koos wat de partner overhoudt (klantprijs min commissie), per partner-ID. Nummer 1 is Sushi De Smaak (Amsterdam), €36.226,63. | Ja |
| 4 | "Beste maand met indicatie waarom" | **Maart 2025, €56.099,56.** Reden: meer verkopen (4.410), vouchers en actieve deals dan elke andere maand. Zei erbij dat de echte oorzaak niet in de data staat. | Ja |
| 5 | "Slechtste maand met indicatie waarom" | **September 2026, €30.616,83.** Liet oktober 2026 buiten beschouwing, want die heeft maar 5 verkopen. Reden: minste verkopen en actieve partners, lagere commissie per verkoop, en een dalende trend sinds februari 2026. | Ja |

## Wat ging er mis?

Weinig. De antwoorden klopten met de database. Drie dingen vielen op:

1. **Geen periode in de vraag.** Claude koos zelf de hele dataset. Dat is een aanname die Claude erbij noemde.
2. **Dubbelzinnige vragen.** "Winst", "uitgave" en "opbrengst voor partners" kunnen meerdere dingen betekenen. Claude noemde zelf welke betekenis het gebruikte.
3. **Een tool was niet genoeg voor de verklaring.** Voor vraag 4 en 5 (verkopen en partners per maand) was SQL nodig. `omzet_per_maand` geeft alleen de omzet.

## Wat ik aanpaste

- **`business_context` aangepast:** erbij gezet dat antwoorden altijd moeten steunen op de waarheid en de cijfers uit de database, en niet op aannames.

## Mogelijke verbeteringen (nog niet doorgevoerd)

- In de tool-beschrijving zetten wat de tool **niet** kan (geen winst, klanten, partners of maanden), zodat Claude sneller doorverwijst.
- Een duidelijke foutmelding bij een periode langer dan 1 jaar, met de tip om de vraag in meerdere stukken te splitsen.

## Beperking

De test is gedaan met alle starterkit-tools gekoppeld. Een test met uitsluitend de eigen `omzet_per_stad` uit deel 1 is niet gedaan.
