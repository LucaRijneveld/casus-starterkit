# Mijn uitleg bij de Social Deal-data

## Welke database gebruik ik?

In deze casus werk ik met twee SQLite-databases:

- `socialdeal_casus.sqlite` is de brondatabase. Hierin staat de originele, bewust niet helemaal schone data, inclusief kolommen met klantgegevens.
- `socialdeal_clean.sqlite` is de opgeschoonde kopie die ik gebruik voor rapportages. Direct herkenbare klantgegevens zijn eruit gehaald en er zijn velden toegevoegd die rapporteren makkelijker maken.

Ik gebruik de tools in `revenue.py` als interface voor deze casus. `src_sql` is gekoppeld aan de brondatabase en `clean_sql` aan de opgeschoonde database. Ik ga er niet van uit dat er ook een aparte, algemene SQL-tool of bredere database-toegang beschikbaar is.

Ik gebruik de querytools alleen voor gerichte, alleen-lezen controles. Ik voer geen opdrachten uit die data wijzigen en haal geen direct herkenbare klantgegevens op uit de brondatabase. Ik zet zulke gegevens ook niet in uitvoer of logs.

## Zo wil ik dat antwoorden worden onderbouwd

Ik wil dat alle redeneringen, uitleg en conclusies steunen op gegevens die echt in deze databases staan of die de tools teruggeven. Ik verzin geen cijfers en presenteer aannames niet als feiten. Als de data geen antwoord geeft, benoem ik duidelijk wat er ontbreekt.

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

`klant_email` en `betaalreferentie` zijn persoonsgegevens of betaalgegevens. Ik gebruik ze niet in queryresultaten, tooluitvoer, foutmeldingen of logs. Voor analyses gebruik ik bij voorkeur de clean database.

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

- `klant_id`: een gepseudonimiseerde, gezouten hash op basis van het e-mailadres. Voor omzetrapportages heb ik dit veld niet nodig; ik behandel het als gevoelig en toon het niet.
- `status_clean`: opgeschoonde status in kleine letters (`betaald`, `geannuleerd` of `terugbetaald`), zonder spaties aan het begin of einde.
- `partner_is_test`: geeft aan of de verkoop bij een testpartner hoort.
- `telt_mee_voor_omzet`: is `1` voor betaalde verkopen van niet-testpartners, en anders `0`.
- `aangemaakt_op_nl` en `verwerkt_op_nl`: aanmaak- en verwerkingstijd omgerekend naar Europe/Amsterdam. In het bouwscript ga ik standaard uit van UTC als brontijdzone.

Bij het bouwen van de clean database herstel ik veelvoorkomende tekstproblemen, maak ik statussen gelijkvormig, zet ik tijdstempels om en laat ik directe klantgegevens weg. Ik sla de aantallen opgeschoonde waarden op in `dq_log`. De bedragen blijven zoals ze in de bron staan; ik vermenigvuldig ze niet met het aantal vouchers.

## De regels die ik voor omzet gebruik

- Omzet is de commissie van Social Deal: de som van `commissie_cent`. `klantprijs_cent` is wat de klant betaalt en is dus geen omzet.
- Alleen betaalde verkopen van niet-testpartners tellen mee. In de clean database gebruik ik hiervoor `telt_mee_voor_omzet = 1` of de view `omzet_verkopen`.
- Ik reken een verkoop toe aan het moment van kopen (`aangemaakt_op`), niet aan het moment van verwerken (`verwerkt_op`).
- Voor rapportagedatums gebruik ik de Amsterdamse tijd in `aangemaakt_op_nl`.
- De periode is inclusief: zowel de begin- als einddatum tellen mee.
- Eén verkoopregel kan meerdere vouchers (`aantal`) bevatten. `commissie_cent` en `klantprijs_cent` zijn al totalen voor de hele regel; ik vermenigvuldig ze dus niet nog eens met `aantal`.
- Ik reken een verkoop toe aan de stad van de partner.
- Bedragen zijn gehele centen. Voor bedragen in euro's deel ik door 100.

## Steden met dezelfde naam

In de data komen verschillende steden met dezelfde naam voor, zoals Bergen en Laren. `omzet_per_stad` groepeert daarom op stad-ID en niet alleen op naam. De uitvoer laat ook de stad-ID, naam, het land en de regio zien, zodat ik de steden uit elkaar kan houden.

## Partners met dezelfde naam

Partnernamen zijn niet uniek: dezelfde naam kan bij meerdere partner-ID's voorkomen, ook in dezelfde stad. Uit de data kan ik niet afleiden of die ID's bij hetzelfde bedrijf horen of bij aparte partnerregistraties.

`omzet_per_partner` en `top_partners` geven daarom voor de gekozen periode twee overzichten, allebei gesorteerd op omzet van hoog naar laag:

1. **Partners apart op ID:** één regel per partner-ID, met de naam en stad. Ik gebruik dit overzicht als ik individuele partnerregistraties wil vergelijken.
2. **Samengevoegd op exacte partnernaam en stad:** regels met precies dezelfde naam en stad worden bij elkaar opgeteld. Dat is handig als totaaloverzicht, maar bewijst niet dat de ID's bij hetzelfde bedrijf horen. Partners in verschillende steden voeg ik niet samen.

Beide tools passen de limiet per overzicht toe. `omzet_per_partner` toont standaard de top 5 per overzicht; met `n` kan ik een ander aantal opvragen. `top_partners` gebruikt ook standaard 5 per overzicht. Als het verschil tussen partnerregistraties belangrijk is, gebruik ik het overzicht per ID.

## De tools die ik gebruik

Ik gebruik eerst `data_context`, zodat de regels en definities duidelijk zijn. Voor gewone omzetvragen gebruik ik de tools op de clean database. De reconciliatietools gebruik ik om verschillen te onderzoeken; hun alternatieve scenario's zijn niet de officiële omzetdefinitie.

| Tool | Invoer | Wat ik ermee doe |
| --- | --- | --- |
| `data_context` | geen | Geeft deze uitleg terug. Zo staan de tabellen, definities en afspraken bij elkaar voordat ik de andere tools gebruik. |
| `exploratory_data_analysis` | geen | Geeft de schema's, aantallen rijen, aantallen unieke numerieke waarden, aantallen NULL-waarden en enkele voorbeeldrijen uit de brondatabase. Ik gebruik dit om de structuur en datakwaliteit te verkennen. `klant_email` en `betaalreferentie` worden niet in de voorbeeldrijen getoond. |
| `src_sql` | `query` | Voert een gerichte, alleen-lezen query uit op de brondatabase. Ik gebruik dit om ruwe waarden te onderzoeken of verschillen met de clean database na te gaan. Ik haal nooit persoonsgegevens of betaalgegevens op. |
| `clean_sql` | `query` | Voert een gerichte, alleen-lezen query uit op de clean database. Ik gebruik dit om opgeschoonde waarden te controleren, berekeningen te valideren of `dq_log` te bekijken. Ik toon `klant_id` niet, tenzij een analyse dat nadrukkelijk vereist. |
| `omzet_per_stad` | `start_date`, `end_date` | Telt de meetellende commissie per stad-ID op voor een inclusieve periode in Amsterdamse tijd. De stad-ID, naam, het land en de regio houden gelijknamige steden uit elkaar. |
| `omzet_per_partner` | `start_date`, `end_date`, optioneel `n` (standaard 5) | Geeft voor de inclusieve periode zowel de top `n` per partner-ID als de top `n` samengevoegde regels per exacte naam en stad. Ik gebruik dit om losse partnerregistraties naast een naamoverzicht te leggen. |
| `zoek_stad` | `naam` | Zoekt op een deel van een stadsnaam en toont de stad-ID, naam, land en regio. Ik gebruik dit om een stadsnaam te controleren voordat ik cijfers opvraag. |
| `zoek_partner` | `naam` | Zoekt op een deel van een partnernaam en toont partner-ID, naam, stad en land. Ik gebruik dit om te zien bij welke stad een partner hoort. |
| `beschikbare_periode` | geen | Toont de vroegste en laatste Amsterdamse aanmaaktijd in de clean verkoopdata. Ik controleer hiermee of de gevraagde periode in de dataset valt. |
| `omzet_per_maand` | `start_date`, `end_date` | Groepeert de meetellende commissie per maand binnen een inclusieve periode. Ik gebruik dit om trends en seizoenspatronen te bekijken. |
| `vergelijk_periode` | `start_date_1`, `end_date_1`, `start_date_2`, `end_date_2` | Berekent de meetellende commissie voor twee afzonderlijke inclusieve periodes. Ik gebruik dit om periodes met elkaar te vergelijken. |
| `top_partners` | `start_date`, `end_date`, optioneel `n` (standaard 5) | Geeft de top `n` partner-ID's en de top `n` exacte groepen van naam en stad op basis van commissie in een inclusieve periode. Zo zie ik wie het meest bijdraagt, zonder gelijknamige partners stilzwijgend samen te voegen. |
| `reconciliate_clean` | `start_datum`, `eind_datum` | Geeft de omzet volgens de clean-dataregels en het verschil met een aantal veelvoorkomende alternatieven. Ik gebruik dit om te zien hoeveel een andere datum, testpartners, klantprijs, voucherhoeveelheid of einddatumregel uitmaakt. |
| `reconciliate_rapport` | `start_datum`, `eind_datum`, `bedrag_cent`, optioneel `vouchers` | Probeert alle 128 combinaties van datumsoort en tijdzone, testpartner- en statuskeuze, einddatum, commissie of klantprijs, en wel of niet vermenigvuldigen met het aantal vouchers. Ik krijg alle exacte verklaringen terug, met de minste afwijkingen eerst. Als ik ook vouchers opgeef, moeten bedrag én aantal vouchers overeenkomen. Zonder exacte match toont de tool de drie bedragen die er het dichtst bij zitten. Ik gebruik dit alleen om verschillen te onderzoeken; voor het juiste basisbedrag gebruik ik `reconciliate_clean`. |

Ik geef datums op als `YYYY-MM-DD`. Als er geen resultaten zijn, controleer ik eerst de periode en spelling voordat ik conclusies trek.
