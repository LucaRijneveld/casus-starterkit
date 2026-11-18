#!/usr/bin/env python3
"""
Dit script maakt een schone kopie van de Social Deal-database.

De brondatabase wordt alleen-lezen geopend en de clean database wordt bij elke
run opnieuw opgebouwd. Het script kan dus opnieuw worden uitgevoerd om de kopie
opnieuw te maken.

Gebruik:
    python build_clean_db.py

De clean database bevat:
    clean_steden, clean_partners, clean_deals, clean_verkopen
        Dezelfde kolommen als de brontabellen, met een paar extra velden.
        De Nederlandse tabel- en kolomnamen komen overeen met de bron.
    omzet_verkopen (view)
        Alleen verkopen die meetellen voor omzet (betaald en geen testpartner).
    dq_log
        Een overzicht van de opschoonacties en het aantal geraakte rijen.

Wijzigingen ten opzichte van de bron:
    - Het e-mailadres wordt vervangen door een gehashte `klant_id`.
      `klant_email` en `betaalreferentie` worden niet naar de clean database gekopieerd.
    - Statussen worden gelijkvormig gemaakt ("Betaald", "BETAALD", "betaald " -> "betaald").
    - Veelvoorkomende UTF-8-tekstproblemen worden hersteld (bijv. "LiÃ¨ge" -> "Liège").
    - Tijdstempels worden omgezet naar Amsterdamse tijd.
    - Aan clean_verkopen worden toegevoegd:
        klant_id, status_clean, partner_is_test, telt_mee_voor_omzet,
        aangemaakt_op_nl, verwerkt_op_nl
    - Aan clean_deals wordt het veld partner_is_test toegevoegd.

Aan het einde wordt de clean data met de bron vergeleken. Bij een afwijking
stopt het script en verwijdert het de onvolledige clean database.
"""

import hashlib
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# --------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------

SOURCE_DB = Path(os.environ.get("SRC_DB", "socialdeal_casus.sqlite"))
CLEAN_DB = Path(os.environ.get("DST_DB", "socialdeal_clean.sqlite"))

# Timezone the source timestamps are stored in (probably UTC).
SOURCE_TZ = ZoneInfo(os.environ.get("SOURCE_TZ", "UTC"))
TARGET_TZ = ZoneInfo("Europe/Amsterdam")

# Secret used when hashing emails. Keep it outside the database and outside git.
# The same salt always gives the same klant_id for the same email.
SALT = "CleanDBSalt" if os.environ.get("CLEAN_SALT") is None else os.environ.get("CLEAN_SALT")

# Columns that hold personal data and must never be copied to the clean database.
PERSONAL_DATA_COLUMNS = {"klant_email", "betaalreferentie"}

# The only statuses we expect once spaces and capitals are normalized.
# Anything else makes the script stop, so we notice unexpected data.
VALID_STATUSES = {"betaald", "geannuleerd", "terugbetaald"}

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
BATCH_SIZE = 5000  # rows inserted per batch

# Collects "what was changed, and how many rows" for the dq_log table.
dq_counts = {}

def log_change(description, row_count):
    """Telt het aantal aangepaste rijen voor deze regel in `dq_log` op."""
    dq_counts[description] = dq_counts.get(description, 0) + row_count


# --------------------------------------------------------------------------
# Small cleaning helpers (each one fixes exactly one thing)
# --------------------------------------------------------------------------

def fix_broken_text(value):
    """
    Herstelt tekst die als cp1252 is gelezen in plaats van UTF-8
    ("LiÃ¨ge" -> "Liège"). Tekst zonder dit probleem blijft ongewijzigd.
    """
    if isinstance(value, str) and ("Ã" in value or "Â" in value):
        try:
            return value.encode("cp1252").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return value
    return value


def normalize_status(raw_status):
    """Zet de status om naar kleine letters en verwijdert buitenste spaties."""
    status = (raw_status or "").strip().lower()
    if status not in VALID_STATUSES:
        raise SystemExit(f"Unexpected status value: {raw_status!r}")
    return status


def to_amsterdam_time(timestamp):
    """Zet een brontijdstempel om naar Amsterdamse tijd; `None` blijft ongewijzigd."""
    if timestamp is None:
        return None
    parsed = datetime.strptime(timestamp, TIMESTAMP_FORMAT).replace(tzinfo=SOURCE_TZ)
    return parsed.astimezone(TARGET_TZ).strftime(TIMESTAMP_FORMAT)


def make_customer_id(email):
    """
    Maakt een gepseudonimiseerde klant-ID met gezouten SHA-256 (de eerste 16 tekens).
    Het e-mailadres wordt eerst omgezet naar kleine letters en ontdaan van spaties.
    Daardoor krijgen
    "A@x.com " en "a@x.com" dezelfde klant-ID.
    """
    normalized = (email or "").strip().lower()
    return hashlib.sha256((SALT + normalized).encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------------------
# Helpers for creating and filling the clean tables
# --------------------------------------------------------------------------

def get_source_columns(con, table):
    """Geeft per bronkolom de naam, het type en de primary-keystatus terug."""
    rows = con.execute(f'PRAGMA src.table_info("{table}")')
    return [(name, col_type or "", pk) for _, name, col_type, _, _, pk in rows]


def create_clean_table(con, table, skip_columns=(), extra_columns=()):
    """
    Maakt `clean_<table>` met de bronkolommen, behalve overgeslagen kolommen.
    Voegt daarna de extra kolommen toe en geeft de gekopieerde kolomnamen terug,
    in dezelfde volgorde.
    """
    copied = [c for c in get_source_columns(con, table) if c[0] not in skip_columns]
    primary_keys = [name for name, _, pk in copied if pk]

    definitions = []
    for name, col_type, _ in copied:
        is_single_pk = len(primary_keys) == 1 and name == primary_keys[0]
        definitions.append(f'"{name}" {col_type}' + (" PRIMARY KEY" if is_single_pk else ""))
    for name, col_type in extra_columns:
        definitions.append(f'"{name}" {col_type}')

    con.execute(f'CREATE TABLE "clean_{table}" ({", ".join(definitions)})')
    return [name for name, _, _ in copied]


def insert_statement(table, column_count):
    """Maakt een INSERT-opdracht met één placeholder per kolom."""
    placeholders = ",".join("?" * column_count)
    return f'INSERT INTO "clean_{table}" VALUES ({placeholders})'


def flush(con, statement, batch):
    """Schrijft de verzamelde batch in één keer weg en maakt hem daarna leeg."""
    con.executemany(statement, batch)
    batch.clear()


# --------------------------------------------------------------------------
# Build steps
# --------------------------------------------------------------------------

def copy_table_with_text_fix(con, table, extra_columns=(), join_sql="", extra_select=""):
    """
    Kopieert een brontabel naar `clean_<table>` en herstelt tekstproblemen.
    Met `join_sql` en `extra_select` kunnen velden uit een andere tabel worden
    toegevoegd, zoals `partner_is_test` aan `clean_deals`. Geeft het aantal
    gekopieerde rijen terug.
    """
    columns = create_clean_table(con, table, extra_columns=extra_columns)
    select_list = ", ".join(f't."{c}"' for c in columns) + extra_select
    query = f'SELECT {select_list} FROM src."{table}" t {join_sql}'

    rows, repaired_values = [], 0
    for original in con.execute(query):
        fixed = tuple(fix_broken_text(v) for v in original)
        repaired_values += sum(1 for before, after in zip(original, fixed) if before != after)
        rows.append(fixed)

    con.executemany(insert_statement(table, len(columns) + len(extra_columns)), rows)
    log_change(f"{table}: values with broken characters repaired", repaired_values)
    return len(rows)


def build_clean_sales(con):
    """
    Bouwt `clean_verkopen` met een klant-ID, opgeschoonde status,
    testpartner-vlag, omzetvlag en Amsterdamse tijdstempels per verkoop.
    Geeft het aantal weggeschreven rijen terug.
    """
    extra_columns = [
        ("klant_id", "TEXT"),
        ("status_clean", "TEXT"),
        ("partner_is_test", "INTEGER"),
        ("telt_mee_voor_omzet", "INTEGER"),  # 1 = paid and not a test partner
        ("aangemaakt_op_nl", "TEXT"),
        ("verwerkt_op_nl", "TEXT"),
    ]
    columns = create_clean_table(con, "verkopen", PERSONAL_DATA_COLUMNS, extra_columns)
    position = {name: i for i, name in enumerate(columns)}  # column name -> index in a row

    # Read the sales plus the two values we need but do not copy as-is:
    # the email (only used to make klant_id) and whether the partner is a test partner.
    select_list = ", ".join(f'v."{c}"' for c in columns)
    query = (
        f"SELECT {select_list}, v.klant_email, p.is_test "
        "FROM src.verkopen v "
        "LEFT JOIN src.deals d ON d.id = v.deal_id "
        "LEFT JOIN src.partners p ON p.id = d.partner_id"
    )
    statement = insert_statement("verkopen", len(columns) + len(extra_columns))

    batch = []
    total = status_changed = from_test_partner = not_counted = 0

    for row in con.execute(query):
        values = list(row[: len(columns)])
        email, partner_is_test = row[-2], row[-1]

        if partner_is_test is None:
            raise SystemExit("Found a sale without a deal or partner; investigate before continuing.")

        raw_status = values[position["status"]]
        status = normalize_status(raw_status)
        counts_towards_revenue = int(status == "betaald" and partner_is_test == 0)

        processed_at = values[position["verwerkt_op"]] if "verwerkt_op" in position else None

        batch.append(tuple(values) + (
            make_customer_id(email),
            status,
            partner_is_test,
            counts_towards_revenue,
            to_amsterdam_time(values[position["aangemaakt_op"]]),
            to_amsterdam_time(processed_at),
        ))

        total += 1
        status_changed += status != raw_status
        from_test_partner += partner_is_test == 1
        not_counted += 1 - counts_towards_revenue

        if len(batch) >= BATCH_SIZE:
            flush(con, statement, batch)
    flush(con, statement, batch)

    log_change("verkopen: status normalized (spaces/capitals)", status_changed)
    log_change("verkopen: sales from test partners", from_test_partner)
    log_change("verkopen: does not count towards revenue (not paid, or test partner)", not_counted)
    log_change("verkopen: personal data columns left out (klant_email, betaalreferentie)", total)
    return total


def build(con):
    """Maakt de clean tabellen, indexen en omzetview en geeft de rij-aantallen terug."""
    row_counts = {
        "steden": copy_table_with_text_fix(con, "steden"),
        "partners": copy_table_with_text_fix(con, "partners"),
        "deals": copy_table_with_text_fix(
            con, "deals",
            extra_columns=[("partner_is_test", "INTEGER")],
            join_sql="LEFT JOIN src.partners p ON p.id = t.partner_id",
            extra_select=", p.is_test",
        ),
        "verkopen": build_clean_sales(con),
    }

    con.execute("CREATE INDEX idx_clean_verkopen_deal ON clean_verkopen(deal_id)")
    con.execute("CREATE INDEX idx_clean_verkopen_nl ON clean_verkopen(aangemaakt_op_nl)")
    con.execute(
        "CREATE VIEW omzet_verkopen AS "
        "SELECT * FROM clean_verkopen WHERE telt_mee_voor_omzet = 1"
    )
    return row_counts


# --------------------------------------------------------------------------
# Checks: compare the clean data against the source
# --------------------------------------------------------------------------

def check(con, row_counts):
    """Stopt met een AssertionError als de clean database niet overeenkomt met de bron."""

    # 1. Same number of rows in every table.
    for table, copied_rows in row_counts.items():
        source_rows = con.execute(f'SELECT COUNT(*) FROM src."{table}"').fetchone()[0]
        clean_rows = con.execute(f'SELECT COUNT(*) FROM "clean_{table}"').fetchone()[0]
        assert source_rows == copied_rows == clean_rows, f"Row count differs for {table}"

    # 2. Money columns are untouched.
    source_money = con.execute(
        "SELECT SUM(commissie_cent), SUM(klantprijs_cent) FROM src.verkopen").fetchone()
    clean_money = con.execute(
        "SELECT SUM(commissie_cent), SUM(klantprijs_cent) FROM clean_verkopen").fetchone()
    assert source_money == clean_money, f"Amounts differ: {source_money} vs {clean_money}"

    # 3. Revenue calculated directly on the source (paid, no test partners)
    #    equals the revenue in the clean view.
    source_revenue = con.execute(
        "SELECT COUNT(*), SUM(v.commissie_cent) FROM src.verkopen v "
        "JOIN src.deals d ON d.id = v.deal_id "
        "JOIN src.partners p ON p.id = d.partner_id "
        "WHERE lower(trim(v.status)) = 'betaald' AND p.is_test = 0").fetchone()
    clean_revenue = con.execute(
        "SELECT COUNT(*), SUM(commissie_cent) FROM omzet_verkopen").fetchone()
    assert source_revenue == clean_revenue, f"Revenue differs: {source_revenue} vs {clean_revenue}"

    # 4. The number of unique customers is the same after hashing.
    source_customers = con.execute(
        "SELECT COUNT(DISTINCT lower(trim(klant_email))) FROM src.verkopen").fetchone()[0]
    clean_customers = con.execute(
        "SELECT COUNT(DISTINCT klant_id) FROM clean_verkopen").fetchone()[0]
    assert source_customers == clean_customers, \
        f"Customer count differs: {source_customers} vs {clean_customers}"

    sales_count, revenue_cents = clean_revenue
    print(f"OK: {sales_count} sales count towards revenue, "
          f"revenue EUR {revenue_cents / 100:,.2f}, {clean_customers} unique customers")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def write_dq_log(con):
    """Slaat de opschoonaantallen, brontijdzone en uitvoertijd op in `dq_log`."""
    con.execute(
        "CREATE TABLE dq_log (description TEXT, row_count INTEGER, source_tz TEXT, created_at TEXT)")
    created_at = datetime.now(TARGET_TZ).strftime(TIMESTAMP_FORMAT)
    con.executemany(
        "INSERT INTO dq_log VALUES (?, ?, ?, ?)",
        [(description, count, str(SOURCE_TZ), created_at) for description, count in dq_counts.items()],
    )


def main():
    if not SOURCE_DB.exists():
        sys.exit(f"Source database not found: {SOURCE_DB}")
    if not SALT:
        sys.exit("Set the CLEAN_SALT environment variable (keep it outside the database).")

    CLEAN_DB.unlink(missing_ok=True)  # always start from scratch

    # Open the new clean database and attach the source as "src", read-only.
    con = sqlite3.connect(f"file:{CLEAN_DB.resolve()}?mode=rwc", uri=True)
    con.execute("ATTACH DATABASE ? AS src", (f"{SOURCE_DB.resolve().as_uri()}?mode=ro",))

    try:
        row_counts = build(con)
        check(con, row_counts)
        write_dq_log(con)
        con.commit()
    except BaseException:
        # Never leave a half-finished clean database behind.
        con.rollback()
        con.close()
        CLEAN_DB.unlink(missing_ok=True)
        raise

    for description, count in dq_counts.items():
        print(f"{count:>8}  {description}")
    con.close()


if __name__ == "__main__":
    main()