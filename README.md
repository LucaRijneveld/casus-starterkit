# Social Deal casus: MCP-server voor omzet per stad

## Starten

De server is geschreven in Python met de officiële MCP Python SDK (pakket `mcp`).

```bash
pip install -r requirements.txt     # afhankelijkheden (o.a. mcp)
pytest                              # alle tests, één commando
python revenue.py                   # optioneel als je desktop gebruikt: start de MCP-server (stdio)
mcp dev revenue.py                  # optioneel: testen in de MCP Inspector (Node.js nodig)
```

`python revenue.py` print niets en wacht op een MCP-client (zoals Claude Desktop). Dat is normaal.
Claude Desktop koppel je met dit blok in `claude_desktop_config.json`:

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

De server leest `socialdeal_clean.sqlite` (read-only).
De uitvoer voor september 2026 staat in `uitkomst_september_2026.csv`.

## Problemen in de data en hoe ik ze vond

- **Statusspelling:** `betaald`, `Betaald`, `BETAALD` en `betaald ` (met spatie). Gevonden met `GROUP BY status`. 965 verkopen zouden anders worden gemist. Opgelost met `status_clean` en `telt_mee_voor_omzet`.
- **Testpartners:** tellen niet mee. In augustus 2026 gaat het om 80 verkopen (€2.052,34). Gevonden bij het uitzoeken van het verschil met Finance.
- **Tijdzone:** tijdstempels staan in UTC, rapportage gaat op Amsterdamse tijd. Dat verschuift verkopen rond middernacht naar een andere dag.
- **Persoonsgegevens:** de brondatabase bevat `klant_email` en `betaalreferentie`. De eerste versie van de EDA-tool toonde die in voorbeeldrijen; dat is weggehaald. Analyse gebeurt op de clean database.
- **Steden met dezelfde naam:** Bergen (NL en BE) en Laren (twee keer, NL). Groeperen op naam geeft 32 in plaats van 34 steden. Gevonden doordat de lijst van de starterkit-tool niet klopte met de stedentabel. Mijn tool groepeert op stad-ID.
- **Partners met dezelfde naam:** 25 combinaties van naam en stad komen meerdere keer voor, bijvoorbeeld Spa de Linde (Breda, ID 242 en 244). De eerste versies van `top_partners` en `omzet_per_partner` telden die samen, ook over steden heen. Nu staat er een weergave per ID en een weergave per naam en stad.
- **Oude omzettool:** `calculate_revenue_orm` telde alleen de exacte schrijfwijze `betaald` en miste daardoor 942 verkopen.
- **Net buiten de periode:** 5 verkopen vallen op 1 oktober 2026 (Amsterdamse tijd), terwijl de dataset tot en met september loopt. Waarschijnlijk zijn het late-avondverkopen van 30 september in UTC.

## AI-tools die ik gebruikte

- **Gemini:** om de opdracht door te nemen, uit te zoeken hoe ik het beste met de SQLite-database in VS Code kon werken, en om te controleren of mijn tools klopten.
- **Claude:** om alle tools te testen en als controle op mijn tekst. Claude voerde ook de SQL-analyse voor deel 2 uit, omdat het read-only SQL-toegang tot de database had. Claude schreef verder conceptteksten voor deel 2, deel 3 en deze README op basis van onze gesprekken, en een schets van de tool `reconciliate_rapport`.
- Alle cijfers komen uit de database, niet uit het model. In `business_context` staat dat antwoorden altijd daarop moeten steunen.