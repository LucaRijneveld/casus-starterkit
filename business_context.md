# Context bij de Social Deal-data

## De databases

Voor deze casus zijn er twee SQLite-databases:

- `socialdeal_casus.sqlite` is de brondatabase. Hierin staat de originele, bewust niet helemaal schone data, inclusief kolommen met klantgegevens.
- `socialdeal_clean.sqlite` is de opgeschoonde kopie voor rapportages. Direct herkenbare klantgegevens zijn eruit gehaald en er zijn velden toegevoegd die rapporteren makkelijker maken.

De tools in `revenue.py` vormen de interface voor deze casus. `src_sql` is gekoppeld aan de brondatabase en `clean_sql` aan de opgeschoonde database. Er is geen aparte, algemene SQL-tool of bredere database-toegang beschikbaar.

De querytools zijn bedoeld voor gerichte, alleen-lezen controles. Voer geen opdrachten uit die data wijzigen. Haal geen direct herkenbare klantgegevens op uit de brondatabase en zet die niet in uitvoer of logs.

## Onderbouwing van antwoorden

Baseer alle redeneringen, uitleg en conclusies op gegevens die echt in deze databases staan of die de tools teruggeven. Verzin geen cijfers en presenteer aannames niet als feiten. Als de data geen antwoord geeft, benoem dan duidelijk wat er ontbreekt.

## De brondataset

`socialdeal_casus.sqlite` bevat verzonnen gegevens van oktober 2024 tot en met september 2026, met ongeveer 97.000 verkopen.

| Tabel | Aantal rijen (ongeveer) | Belangrijke kolommen |
| --- | ---: | --- |
| `steden` | 34 | `id`, `naam`, `land` (NL/BE), `regio` |
| `partners` | 613 | `id`, `naam`, `stad_id`, `is_test` |
| `deals` | 2.444 | `id`, `partner_id`, `titel`, `start_datum`, `eind_datum`, `prijs_cent`, `commissie_pct` |
| `verkopen` | 96.947 | `id`, `deal_id`, `aangemaakt_op`, `verwerkt_op`, `status`, `aantal`, `klantprijs_cent`, `commissie_cent`, `klant_email`, `betaalreferentie` |

De tabellen zijn zo gekoppeld:

- `verkopen.deal_id` → `deals.id`
- `deals.partner_id` → `partners.id`
- `partners.stad_id` → `steden.id`

`klant_email` en `betaalreferentie` zijn persoonsgegevens of betaalgegevens. Neem ze niet op in queryresultaten, tooluitvoer, foutmeldingen of logs. Gebruik voor analyses bij voorkeur de clean database.

## De clean database

De opgeschoonde database gebruikt dezelfde tabelnamen met het voorvoegsel `clean_` en bevat extra velden voor rapportages:

| Tabel of view | Wat erin staat |
| --- | --- |
| `clean_steden` | `id`, `naam`, `land`, `regio`; tekstproblemen zijn waar mogelijk hersteld. |
| `clean_partners` | `id`, `naam`, `stad_id`, `is_test`; tekstproblemen in partnernamen zijn waar mogelijk hersteld. |
| `clean_deals` | De dealvelden uit de brondatabase, plus `partner_is_test` van de bijbehorende partner. |
| `clean_verkopen` | Verkoopvelden zonder `klant_email` en `betaalreferentie`, plus de afgeleide velden hieronder. |
| `omzet_verkopen` | Een view met alleen regels waarvoor `telt_mee_voor_omzet = 1`. |
| `dq_log` | Overzicht van opschoonacties met `description`, `row_count`, `source_tz` en `created_at`. |

In `clean_verkopen` zijn deze velden toegevoegd:

- `klant_id`: een gepseudonimiseerde, gezouten hash op basis van het e-mailadres. Dit veld is niet nodig voor omzetrapportages; behandel het als gevoelig en toon het niet.
- `status_clean`: opgeschoonde status in kleine letters (`betaald`, `geannuleerd` of `terugbetaald`), zonder spaties aan het begin of einde.
- `partner_is_test`: geeft aan of de verkoop bij een testpartner hoort.
- `telt_mee_voor_omzet`: is `1` voor betaalde verkopen van niet-testpartners, en anders `0`.
- `aangemaakt_op_nl` en `verwerkt_op_nl`: aanmaak- en verwerkingstijd omgerekend naar Europe/Amsterdam. Het bouwscript gaat standaard uit van UTC als brontijdzone.

Bij het bouwen van de clean database worden veelvoorkomende tekstproblemen hersteld, statussen gelijkvormig gemaakt, tijdstempels omgezet en directe klantgegevens weggelaten. De aantallen opgeschoonde waarden staan in `dq_log`. Bedragen blijven zoals ze in de bron staan; ze worden niet vermenigvuldigd met het aantal vouchers.

## Omzetregels

- Omzet is de commissie van Social Deal: de som van `commissie_cent`. `klantprijs_cent` is wat de klant betaalt en is dus geen omzet.
- Alleen betaalde verkopen van niet-testpartners tellen mee. In de clean database wordt dit aangegeven met `telt_mee_voor_omzet = 1` of de view `omzet_verkopen`.
- Een verkoop hoort bij het moment van kopen (`aangemaakt_op`), niet bij het moment van verwerken (`verwerkt_op`).
- Gebruik voor rapportagedatums de Amsterdamse tijd in `aangemaakt_op_nl`.
- De periode is inclusief: zowel de begin- als einddatum tellen mee.
- Eén verkoopregel kan meerdere vouchers (`aantal`) bevatten. `commissie_cent` en `klantprijs_cent` zijn al totalen voor de hele regel; vermenigvuldig ze dus niet nog eens met `aantal`.
- Een verkoop hoort bij de stad van de partner.
- Bedragen zijn gehele centen. Deel bedragen in euro's door 100.

## Steden met dezelfde naam

In de data komen verschillende steden met dezelfde naam voor, zoals Bergen en Laren. `omzet_per_stad` groepeert daarom op stad-ID en niet alleen op naam. De uitvoer toont ook de stad-ID, naam, het land en de regio, zodat gelijknamige steden herkenbaar zijn.

## Partners met dezelfde naam

Partnernamen zijn niet uniek: dezelfde naam kan bij meerdere partner-ID's voorkomen, ook in dezelfde stad. De data laat niet zien of die ID's bij hetzelfde bedrijf horen of bij aparte partnerregistraties.

`omzet_per_partner` en `top_partners` geven daarom voor de gekozen periode twee overzichten, allebei gesorteerd op omzet van hoog naar laag:

1. **Partners apart op ID:** één regel per partner-ID, met de naam en stad. Dit overzicht is bedoeld om individuele partnerregistraties te vergelijken.
2. **Samengevoegd op exacte partnernaam en stad:** regels met precies dezelfde naam en stad worden bij elkaar opgeteld. Dat is handig als totaaloverzicht, maar bewijst niet dat de ID's bij hetzelfde bedrijf horen. Partners in verschillende steden worden niet samengevoegd.

Beide tools passen de limiet per overzicht toe. `omzet_per_partner` en `top_partners` tonen standaard de top 5; met `n` is bij beide tools een ander aantal op te vragen. Gebruik het overzicht per ID als het verschil tussen partnerregistraties belangrijk is.

## De tools

Lees eerst `data_context`, zodat de regels en definities duidelijk zijn. Gebruik voor gewone omzetvragen de tools op de clean database. De reconciliatietools zijn bedoeld om verschillen te onderzoeken; hun alternatieve scenario's zijn niet de officiële omzetdefinitie.

| Tool | Invoer | Functie en gebruik |
| --- | --- | --- |
| `data_context` | geen | Geeft deze uitleg terug. Zo staan de tabellen, definities en afspraken bij elkaar voordat andere tools worden gebruikt. |
| `exploratory_data_analysis` | geen | Geeft de schema's, aantallen rijen, aantallen unieke numerieke waarden, aantallen NULL-waarden en enkele voorbeeldrijen uit de brondatabase. Handig om de structuur en datakwaliteit te verkennen. `klant_email` en `betaalreferentie` worden niet in de voorbeeldrijen getoond. |
| `src_sql` | `query` | Voert een gerichte, alleen-lezen query uit op de brondatabase. Geschikt om ruwe waarden te onderzoeken of verschillen met de clean database na te gaan. Haal geen persoonsgegevens of betaalgegevens op. |
| `clean_sql` | `query` | Voert een gerichte, alleen-lezen query uit op de clean database. Geschikt om opgeschoonde waarden te controleren, berekeningen te valideren of `dq_log` te bekijken. Toon `klant_id` niet, tenzij een analyse dat nadrukkelijk vereist. |
| `omzet_per_stad` | `start_date`, `end_date` | Telt de meetellende commissie per stad-ID op voor een inclusieve periode in Amsterdamse tijd. De stad-ID, naam, het land en de regio houden gelijknamige steden uit elkaar. |
| `omzet_per_partner` | `start_date`, `end_date`, optioneel `n` (standaard 5) | Geeft voor de inclusieve periode zowel de top `n` per partner-ID als de top `n` samengevoegde regels per exacte naam en stad. Handig om losse partnerregistraties naast een naamoverzicht te leggen. |
| `zoek_stad` | `naam` | Zoekt op een deel van een stadsnaam en toont de stad-ID, naam, land en regio. Handig om een stadsnaam te controleren voordat cijfers worden opgevraagd. |
| `zoek_partner` | `naam` | Zoekt op een deel van een partnernaam en toont partner-ID, naam, stad en land. Zo is te zien bij welke stad een partner hoort. |
| `beschikbare_periode` | geen | Toont de vroegste en laatste Amsterdamse aanmaaktijd in de clean verkoopdata. Hiermee is te controleren of de gevraagde periode in de dataset valt. |
| `omzet_per_maand` | `start_date`, `end_date` | Groepeert de meetellende commissie per maand binnen een inclusieve periode. Handig om trends en seizoenspatronen te bekijken. |
| `vergelijk_periode` | `start_date_1`, `end_date_1`, `start_date_2`, `end_date_2` | Berekent de meetellende commissie voor twee afzonderlijke inclusieve periodes. Handig om periodes met elkaar te vergelijken. |
| `top_partners` | `start_date`, `end_date`, optioneel `n` (standaard 5) | Geeft de top `n` partner-ID's en de top `n` exacte groepen van naam en stad op basis van commissie in een inclusieve periode. Zo wordt duidelijk wie het meest bijdraagt, zonder gelijknamige partners stilzwijgend samen te voegen. |
| `reconciliate_clean` | `start_datum`, `eind_datum` | Geeft de omzet volgens de clean-dataregels en het verschil met een aantal veelvoorkomende alternatieven. Laat zien hoeveel een andere datum, testpartners, klantprijs, voucherhoeveelheid of einddatumregel uitmaakt. |
| `reconciliate_rapport` | `start_datum`, `eind_datum`, `bedrag_cent`, optioneel `vouchers` | Probeert alle 128 combinaties van datumsoort en tijdzone, testpartner- en statuskeuze, einddatum, commissie of klantprijs, en wel of niet vermenigvuldigen met het aantal vouchers. De tool geeft exacte verklaringen terug, met de minste afwijkingen eerst. Als ook vouchers worden opgegeven, moeten bedrag én aantal vouchers overeenkomen. Zonder exacte match toont de tool de drie bedragen die er het dichtst bij zitten. Gebruik deze tool alleen om verschillen te onderzoeken; voor het juiste basisbedrag is `reconciliate_clean` bedoeld. |

Datums hebben het formaat `YYYY-MM-DD`. Als er geen resultaten zijn, controleer dan eerst de periode en spelling voordat je conclusies trekt.
