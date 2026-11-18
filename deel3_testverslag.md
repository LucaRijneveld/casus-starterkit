# Deel 3: hoe ik Claude met de MCP-tools heb getest

## Opzet

- Ik stelde Claude de vijf vragen met de MCP-server van de starterkit gekoppeld. Claude kon alle tools gebruiken (onder andere `omzet_per_stad`, `omzet_per_maand`, `top_partners` en `clean_sql`), dus niet alleen `omzet_per_stad`.
- In de vragen noemde ik geen periode. Claude gebruikte de hele dataset (oktober 2024 t/m september 2026).
- Ik controleerde elk antwoord met een eigen SQL-query op de clean database.

## De vijf vragen

| # | Vraag | Wat Claude deed | Klopte het? |
|---|---|---|---|
| 1 | "Totale winst" | Zei dat winst niet kan, want er zijn geen kosten in de data. Gaf in plaats daarvan de totale commissieomzet: **€973.868,69** (82.370 verkopen). | Ja |
| 2 | "Gemiddelde uitgave van een gebruiker" | Gebruikte de **klantprijs** (niet de commissie): **€74,88 per klant** (78.406 klanten), €71,28 per aankoop, €45,82 per voucher. Gebruikte `klant_id` alleen als telling. | Ja |
| 3 | "Opbrengst voor partners, top 5" | Zag dat "opbrengst" twee dingen kan betekenen en koos wat de partner overhoudt (klantprijs min commissie), per partner-ID. Nummer 1 is Sushi De Smaak (Amsterdam), €36.226,63. | Ja |
| 4 | "Beste maand met indicatie waarom" | **Maart 2025, €56.099,56.** Reden: meer verkopen (4.410), vouchers en actieve deals dan elke andere maand. Zei erbij dat de echte oorzaak niet in de data staat. | Ja |
| 5 | "Slechtste maand met indicatie waarom" | **September 2026, €30.616,83.** Liet oktober 2026 buiten beschouwing, want die heeft maar 5 verkopen. Reden: minste verkopen en actieve partners, lagere commissie per verkoop, en een dalende trend sinds februari 2026. | Ja |

## Wat ging er mis?

Er ging weinig mis: de antwoorden klopten met de database. Wel vielen me drie dingen op:

1. **Ik noemde geen periode.** Claude koos daarom zelf de hele dataset en benoemde die aanname.
2. **Mijn vragen waren dubbelzinnig.** "Winst", "uitgave" en "opbrengst voor partners" kunnen meerdere dingen betekenen. Claude legde uit welke betekenis het koos.
3. **Voor de verklaring had ik meer dan één tool nodig.** Voor vraag 4 en 5 (verkopen en partners per maand) gebruikte ik SQL. `omzet_per_maand` geeft alleen de omzet.

## Wat ik aanpaste

- **`business_context` aangepast:** ik heb erin gezet dat antwoorden moeten steunen op de cijfers uit de database, niet op aannames.

## Mogelijke verbeteringen (nog niet doorgevoerd)

- In de tool-beschrijving zetten wat de tool **niet** kan (geen winst, klanten, partners of maanden), zodat Claude sneller doorverwijst.
- Een duidelijke foutmelding bij een periode langer dan 1 jaar, met de tip om de vraag in meerdere stukken te splitsen.

## Beperking

Ik heb getest met alle starterkit-tools gekoppeld. Ik heb niet getest met alleen mijn eigen `omzet_per_stad` uit deel 1.
