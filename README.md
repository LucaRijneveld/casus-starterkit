# Mijn Social Deal-casus: MCP-server voor omzet per stad

## Starten

Ik heb de server in Python gebouwd met de officiële MCP Python SDK (pakket `mcp`).

```bash
pip install -r requirements.txt     # afhankelijkheden (o.a. mcp)
pytest                              # alle tests, één commando
python revenue.py                   # optioneel als je desktop gebruikt: start de MCP-server (stdio)
mcp dev revenue.py                  # optioneel: testen in de MCP Inspector (Node.js nodig)
```

Als ik `python revenue.py` start, print de server niets maar wacht hij op een MCP-client, zoals Claude Desktop. Dat is normaal.
Ik koppel Claude Desktop met dit blok in `claude_desktop_config.json`:

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
Ik heb de uitvoer voor september 2026 opgeslagen in `uitkomst_september_2026.csv`.

## Problemen in de data en hoe ik ze vond

- **Statusspelling:** ik vond `betaald`, `Betaald`, `BETAALD` en `betaald ` (met spatie) met `GROUP BY status`. Zonder opschonen zouden 965 verkopen worden gemist. Ik heb dit opgelost met `status_clean` en `telt_mee_voor_omzet`.
- **Testpartners:** die tellen niet mee. In augustus 2026 gaat het om 80 verkopen (€2.052,34). Ik kwam dit tegen toen ik het verschil met Finance onderzocht.
- **Tijdzone:** de tijdstempels staan in UTC, maar ik rapporteer in Amsterdamse tijd. Daardoor vallen verkopen rond middernacht soms op een andere dag.
- **Persoonsgegevens:** de brondatabase bevat `klant_email` en `betaalreferentie`. In de eerste versie van mijn EDA-tool stonden die in de voorbeeldrijen; ik heb ze daaruit verwijderd. Voor analyses gebruik ik de clean database.
- **Steden met dezelfde naam:** Bergen komt voor in NL en BE, en Laren twee keer in NL. Groeperen op naam geeft 32 in plaats van 34 steden. Ik ontdekte dit toen de lijst van de starterkit-tool niet overeenkwam met de stedentabel. Mijn tool groepeert nu op stad-ID.
- **Partners met dezelfde naam:** 25 combinaties van naam en stad komen meer dan één keer voor, bijvoorbeeld Spa de Linde in Breda (ID 242 en 244). De eerste versies van `top_partners` en `omzet_per_partner` telden die samen, soms ook over steden heen. Nu toon ik een weergave per ID en een weergave per naam en stad.
- **Oude omzettool:** `calculate_revenue_orm` telde alleen de exacte schrijfwijze `betaald` en miste daardoor 942 verkopen.
- **Net buiten de periode:** 5 verkopen vallen in Amsterdamse tijd op 1 oktober 2026, terwijl de dataset tot en met september loopt. Waarschijnlijk zijn dit late verkopen van 30 september in UTC.

## AI-tools die ik heb gebruikt

- **Gemini:** ik gebruikte Gemini om de opdracht door te nemen, uit te zoeken hoe ik met de SQLite-database in VS Code kon werken en mijn tools te controleren.
- **Claude:** ik gebruikte Claude om alle tools te testen en mijn teksten na te kijken. Claude deed ook de SQL-analyse voor deel 2, omdat het read-only toegang had tot de database. Op basis van onze gesprekken maakte Claude conceptteksten voor deel 2, deel 3 en deze README, plus een schets voor `reconciliate_rapport`.
- Alle cijfers in mijn uitwerking komen uit de database, niet uit het model. In `business_context` heb ik vastgelegd dat antwoorden op de data moeten steunen.