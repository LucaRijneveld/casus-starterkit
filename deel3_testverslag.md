# Deel 3: Claude testen met de MCP-tools

## Opzet

- Claude kreeg de vijf vragen met de MCP-server van de starterkit gekoppeld. Alle tools waren beschikbaar, waaronder `omzet_per_stad`, `omzet_per_maand`, `top_partners` en `clean_sql`; de test beperkte zich dus niet tot `omzet_per_stad`.
- De vragen noemden geen periode. Claude gebruikte daarom de hele dataset (oktober 2024 t/m september 2026).
- Elk antwoord is gecontroleerd met een SQL-query op de clean database.

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

1. **Er was geen periode genoemd.** Claude koos daarom zelf de hele dataset en benoemde die aanname.
2. **De vragen waren dubbelzinnig.** "Winst", "uitgave" en "opbrengst voor partners" kunnen meerdere dingen betekenen. Claude legde uit welke betekenis het koos.
3. **Voor de verklaring waren meerdere tools nodig.** Voor vraag 4 en 5 (verkopen en partners per maand) was SQL nodig, omdat `omzet_per_maand` alleen de omzet geeft.

## Aanpassing

- In `business_context` staat nu dat antwoorden moeten steunen op cijfers uit de database, niet op aannames.

## Mogelijke verbeteringen (nog niet doorgevoerd)

- In de tool-beschrijving zetten wat de tool **niet** kan (geen winst, klanten, partners of maanden), zodat Claude sneller doorverwijst.
- Een duidelijke foutmelding bij een periode langer dan 1 jaar, met de tip om de vraag in meerdere stukken te splitsen.

## Beperking

De test is uitgevoerd met alle starterkit-tools gekoppeld. De eigen tool `omzet_per_stad` uit deel 1 is niet afzonderlijk getest.
