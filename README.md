# Social Deal-casus: MCP-server voor omzet per stad

## Starten

De server is in Python gebouwd met de officiële MCP Python SDK (pakket `mcp`).

```bash
pip install -r requirements.txt     # afhankelijkheden (o.a. mcp)
pytest                              # alle tests, één commando
python revenue.py                   # optioneel als je desktop gebruikt: start de MCP-server (stdio)
mcp dev revenue.py                  # optioneel: testen in de MCP Inspector (Node.js nodig)
```

Als `python revenue.py` start, print de server niets maar wacht hij op een MCP-client, zoals Claude Desktop. Dat is normaal.
Koppel Claude Desktop met dit blok in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "social-deal-revenue": {
      "command": "python",
      "args": ["C:\\pad\\naar\\casus-starterkit\\revenue.py"]
    }
  }
}
```

De server gebruikt `socialdeal_clean.sqlite` alleen om data te lezen.
De uitvoer voor september 2026 staat in `uitkomst_september_2026.csv`.

## Problemen in de data

- **Statusspelling:** met `GROUP BY status` kwamen `betaald`, `Betaald`, `BETAALD` en `betaald ` (met spatie) naar voren. Zonder opschonen zouden 965 verkopen worden gemist. `status_clean` en `telt_mee_voor_omzet` zorgen nu voor een eenduidige status.
- **Testpartners:** testpartners tellen niet mee. In augustus 2026 gaat het om 80 verkopen (€2.052,34). Dit kwam aan het licht bij het onderzoeken van het verschil met Finance.
- **Tijdzone:** de tijdstempels staan in UTC, terwijl rapportages Amsterdamse tijd gebruiken. Daardoor vallen verkopen rond middernacht soms op een andere dag.
- **Persoonsgegevens:** de brondatabase bevat `klant_email` en `betaalreferentie`. Die stonden in de eerste versie van de EDA-tool in de voorbeeldrijen, maar zijn daaruit verwijderd. Voor analyses wordt de clean database gebruikt.
- **Steden met dezelfde naam:** Bergen komt voor in NL en BE, en Laren twee keer in NL. Groeperen op naam geeft 32 in plaats van 34 steden. Dat bleek toen de lijst van de starterkit-tool niet overeenkwam met de stedentabel. De eigen tool groepeert daarom op stad-ID.
- **Partners met dezelfde naam:** 25 combinaties van naam en stad komen meer dan één keer voor, bijvoorbeeld Spa de Linde in Breda (ID 242 en 244). De eerste versies van `top_partners` en `omzet_per_partner` telden die samen, soms ook over steden heen. De huidige uitvoer toont zowel een weergave per ID als een weergave per naam en stad.
- **Oude omzettool:** `calculate_revenue_orm` telde alleen de exacte schrijfwijze `betaald` en miste daardoor 942 verkopen.
- **Net buiten de periode:** 5 verkopen vallen in Amsterdamse tijd op 1 oktober 2026, terwijl de dataset tot en met september loopt. Waarschijnlijk zijn dit late verkopen van 30 september in UTC.

## AI-tools

Tijdens het uitwerken gebruikte ik Gemini om de opdracht door te nemen, met de SQLite-database in VS Code te werken en de tools te controleren. Claude hielp met het testen van de tools en het nakijken van de teksten. Ook deed Claude de SQL-analyse voor deel 2, met read-only toegang tot de database. Op basis van onze gesprekken maakte Claude conceptteksten voor deel 2, deel 3 en deze README, en een schets voor `reconciliate_rapport`.

Alle cijfers in deze uitwerking komen uit de database, niet uit het model. In `business_context` staat dat antwoorden op de beschikbare data moeten steunen.