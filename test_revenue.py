import pytest
from pathlib import Path
from unittest.mock import patch
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Import the necessary components from sqldatabase.py
from sqldatabase import engine, Stad, Partner, Deal, Verkoop

engine_src = engine  # Use the engine from sqldatabase.py (socialdeal_casus.sqlite)
engine_clean = create_engine(f"sqlite:///{Path(__file__).parent / 'socialdeal_clean.sqlite'}")  # Use this engine for the cleaned up database

def test_data_context():
    """Ik controleer of mijn business context bestaat en leesbaar is."""
    context_file = Path(__file__).parent / "business_context.md"
    assert context_file.exists(), "Business context file does not exist."
    assert context_file.is_file(), "Business context path is not a file."
    with open(context_file, 'r', encoding='utf-8') as f:
        content = f.read()
        assert len(content) > 0, "Business context file is empty."

# All Source database tests are below. Including tool function tests.
def test_src_database_connection():
    """Ik controleer of ik verbinding kan maken met de brondatabase."""
    try:
        with Session(engine_src) as session:
            # Execute a simple query to test the connection
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")

def test_src_Stad_table_count():
    """Ik controleer of de tabel `steden` bestaat en rijen bevat."""
    with Session(engine_src) as session:
        result = session.execute(text("SELECT COUNT(*) FROM steden;"))
        count = result.scalar()
        assert count > 0, "Table 'steden' is empty."

def test_src_Partner_table_count():
    """Ik controleer of de tabel `partners` bestaat en rijen bevat."""
    with Session(engine_src) as session:
        result = session.execute(text("SELECT COUNT(*) FROM partners;"))
        count = result.scalar()
        assert count > 0, "Table 'partners' is empty."  

def test_src_Deal_table_count():
    """Ik controleer of de tabel `deals` bestaat en rijen bevat."""
    with Session(engine_src) as session:
        result = session.execute(text("SELECT COUNT(*) FROM deals;"))
        count = result.scalar()
        assert count > 0, "Table 'deals' is empty."

def test_src_Verkoop_table_count():
    """Ik controleer of de tabel `verkopen` bestaat en rijen bevat."""
    with Session(engine_src) as session:
        result = session.execute(text("SELECT COUNT(*) FROM verkopen;"))
        count = result.scalar()
        assert count > 0, "Table 'verkopen' is empty."

def  test_exploratory_data_analysis():
    """Ik controleer of mijn EDA-tool zonder fouten draait."""
    from revenue import exploratory_data_analysis
    try:
        result = exploratory_data_analysis()
        assert "Found" in result, "Exploratory data analysis did not return expected output."
    except Exception as e:
        pytest.fail(f"Exploratory data analysis tool failed: {e}")

def test_exploratory_data_analysis_omits_sensitive_sample_values():
    """Ik controleer dat EDA geen e-mailadressen of betaalreferenties toont."""
    import revenue

    test_engine = create_engine("sqlite://")
    with test_engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE verkopen (id INTEGER, klant_email TEXT, "
            "betaalreferentie TEXT, status TEXT)"
        ))
        connection.execute(text(
            "INSERT INTO verkopen VALUES "
            "(1, 'private@example.invalid', 'PAYMENT-SECRET', 'betaald')"
        ))

    try:
        with patch.object(revenue, "engine_src", test_engine):
            result = revenue.exploratory_data_analysis()
    finally:
        test_engine.dispose()

    assert "private@example.invalid" not in result
    assert "PAYMENT-SECRET" not in result
    assert "Sensitive columns omitted: klant_email, betaalreferentie" in result
    assert "betaald" in result

def test_src_sql_query_tool():
    """Ik controleer of de querytool voor de brondatabase werkt."""
    from revenue import src_sql
    test_query = "SELECT 1"
    try:
        result = src_sql(test_query)
        assert result == [(1,)], "SQL query tool did not return expected output."
    except Exception as e:
        pytest.fail(f"SQL query tool failed: {e}") 
      
# All Clean database tests are below. Including tool function tests.  
def test_clean_database_connection():
    """Ik controleer of ik verbinding kan maken met de clean database."""
    try:
        with Session(engine_clean) as session:
            # Execute a simple query to test the connection
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1
    except Exception as e:
        pytest.fail(f"Clean database connection failed: {e}")

def test_clean_Stad_table_count():
    """Ik controleer of `clean_steden` bestaat en rijen bevat."""
    with Session(engine_clean) as session:
        result = session.execute(text("SELECT COUNT(*) FROM clean_steden;"))
        count = result.scalar()
        assert count > 0, "Table 'clean_steden' is empty."

def test_clean_Partner_table_count():
    """Ik controleer of `clean_partners` bestaat en rijen bevat."""
    with Session(engine_clean) as session:
        result = session.execute(text("SELECT COUNT(*) FROM clean_partners;"))
        count = result.scalar()
        assert count > 0, "Table 'clean_partners' is empty."

def test_clean_Deal_table_count():
    """Ik controleer of `clean_deals` bestaat en rijen bevat."""
    with Session(engine_clean) as session:
        result = session.execute(text("SELECT COUNT(*) FROM clean_deals;"))
        count = result.scalar()
        assert count > 0, "Table 'clean_deals' is empty."

def test_clean_Verkoop_table_count():
    """Ik controleer of `clean_verkopen` bestaat en rijen bevat."""
    with Session(engine_clean) as session:
        result = session.execute(text("SELECT COUNT(*) FROM clean_verkopen;"))
        count = result.scalar()
        assert count > 0, "Table 'clean_verkopen' is empty."

def test_clean_sql_query_tool():
    """Ik controleer of de querytool voor de clean database werkt."""
    from revenue import sql_query_tool
    test_query = "SELECT 1"
    try:
        result = sql_query_tool(test_query)
        assert result == [(1,)], "SQL query tool did not return expected output on clean database."
    except Exception as e:
        pytest.fail(f"SQL query tool failed on clean database: {e}")

def test_omzet_per_stad_tool():
    """Ik controleer of mijn tool voor omzet per stad werkt."""
    from revenue import omzet_per_stad
    try:
        result = omzet_per_stad(start_date="2025-01-01", end_date="2025-12-31")
        assert "Omzet per stad" in result, "Omzet per stad tool did not return expected output."
    except Exception as e:
        pytest.fail(f"Omzet per stad tool failed: {e}")

def test_omzet_per_partner_tool():
    """Ik controleer of mijn tool voor omzet per partner werkt."""
    from revenue import omzet_per_partner
    try:
        result = omzet_per_partner(start_date="2025-01-01", end_date="2025-12-31")
        assert "Omzet per partner" in result, "Omzet per partner tool did not return expected output."
    except Exception as e:
        pytest.fail(f"Omzet per partner tool failed: {e}")

def test_partner_revenue_reports_show_id_and_combined_name_city_totals():
    """Ik controleer of dubbele partnernamen apart en samengevoegd terugkomen."""
    import cleandatabase
    import revenue

    test_engine = create_engine("sqlite://")
    cleandatabase.Base.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        session.add_all([
            cleandatabase.Stad(
                id=1, naam="Utrecht", land="NL", regio="Midden-Nederland"
            ),
            cleandatabase.Partner(
                id=10, naam="Duplicate Partner", stad_id=1, is_test=0
            ),
            cleandatabase.Partner(
                id=11, naam="Duplicate Partner", stad_id=1, is_test=0
            ),
            cleandatabase.Deal(
                id=100, partner_id=10, titel="Deal 1",
                start_datum="2025-01-01", eind_datum="2025-12-31",
                prijs_cent=10000, commissie_pct=20.0, partner_is_test=0,
            ),
            cleandatabase.Deal(
                id=101, partner_id=11, titel="Deal 2",
                start_datum="2025-01-01", eind_datum="2025-12-31",
                prijs_cent=10000, commissie_pct=20.0, partner_is_test=0,
            ),
            cleandatabase.Verkoop(
                id=1000, deal_id=100, aangemaakt_op="2025-03-15 12:00:00",
                verwerkt_op="2025-03-15 12:00:00", status="betaald",
                aantal=1, klantprijs_cent=100000, commissie_cent=23020,
                klant_id="test-customer-1", status_clean="betaald",
                partner_is_test=0, telt_mee_voor_omzet=1,
                aangemaakt_op_nl="2025-03-15 13:00:00",
                verwerkt_op_nl="2025-03-15 13:00:00",
            ),
            cleandatabase.Verkoop(
                id=1001, deal_id=101, aangemaakt_op="2025-03-15 12:00:00",
                verwerkt_op="2025-03-15 12:00:00", status="betaald",
                aantal=1, klantprijs_cent=100000, commissie_cent=12000,
                klant_id="test-customer-2", status_clean="betaald",
                partner_is_test=0, telt_mee_voor_omzet=1,
                aangemaakt_op_nl="2025-03-15 13:00:00",
                verwerkt_op_nl="2025-03-15 13:00:00",
            ),
        ])
        session.commit()

    try:
        with patch.object(revenue, "engine_clean", test_engine):
            partner_revenue = revenue.omzet_per_partner(
                "2025-01-01", "2025-12-31"
            )
            top_partners = revenue.top_partners(
                "2025-01-01", "2025-12-31"
            )
    finally:
        test_engine.dispose()

    for result in (partner_revenue, top_partners):
        assert "Separate partners (by ID)" in result
        assert "Combined by exact partner name and city" in result
        assert "10\tDuplicate Partner\tUtrecht\t23020" in result
        assert "11\tDuplicate Partner\tUtrecht\t12000" in result
        assert "Duplicate Partner\tUtrecht\t35020" in result
        
def test_zoek_stad_tool():
    """Ik controleer of mijn zoektool voor steden werkt."""
    from revenue import zoek_stad
    test_stad = "Amsterdam"
    try:
        result = zoek_stad(test_stad)
        assert test_stad in result, "Zoek stad tool did not return expected output."
        assert "ID\tNaam\tLand\tRegio" in result
    except Exception as e:
        pytest.fail(f"Zoek stad tool failed: {e}")  
        
def test_zoek_partner_tool():
    """Ik controleer of mijn zoektool voor partners werkt."""
    from revenue import zoek_partner
    with Session(engine_clean) as session:
        test_partner = session.execute(
            text("SELECT naam FROM clean_partners LIMIT 1")
        ).scalar_one()
    try:
        result = zoek_partner(test_partner)
        assert test_partner in result, "Zoek partner tool did not return expected output."
        assert "ID\tPartner\tStad\tLand" in result
    except Exception as e:
        pytest.fail(f"Zoek partner tool failed: {e}")

def test_beschikbare_periode_tool():
    """Ik controleer of mijn tool de beschikbare periode teruggeeft."""
    from revenue import beschikbare_periode
    try:
        result = beschikbare_periode()
        assert "Beschikbare periode" in result, "Beschikbare periode tool did not return expected output."
    except Exception as e:
        pytest.fail(f"Beschikbare periode tool failed: {e}")
        
def test_omzet_per_maand_tool():
    """Ik controleer of mijn tool voor omzet per maand werkt."""
    from revenue import omzet_per_maand
    test_start_date = "2025-01-01"
    test_end_date = "2025-12-31"
    try:
        result = omzet_per_maand(test_start_date, test_end_date)
        assert "Omzet per maand" in result, "Omzet per maand tool did not return expected output."
    except Exception as e:
        pytest.fail(f"Omzet per maand tool failed: {e}")   

def test_vergelijk_periode_tool():
    """Ik controleer of mijn tool twee periodes kan vergelijken."""
    from revenue import vergelijk_periode
    test_start_date1 = "2025-01-01"
    test_end_date1 = "2025-06-30"
    test_start_date2 = "2025-07-01"
    test_end_date2 = "2025-12-31"
    try:
        result = vergelijk_periode(test_start_date1, test_end_date1, test_start_date2, test_end_date2)
        assert "Vergelijking van periodes" in result, "Vergelijk periode tool did not return expected output."
    except Exception as e:
        pytest.fail(f"Vergelijk periode tool failed: {e}")
        
def test_top_partners_tool():
    """Ik controleer of mijn tool de top-partners kan tonen."""
    from revenue import top_partners
    test_start_date = "2025-01-01"
    test_end_date = "2025-12-31"
    try:
        result = top_partners(test_start_date, test_end_date)
        assert "Top partners" in result, "Top partners tool did not return expected output."
    except Exception as e:
        pytest.fail(f"Top partners tool failed: {e}")   

def test_reconciliate_clean_tool():
    """Ik controleer de clean-omzet en de verschillen met andere rapportageregels."""
    from revenue import reconciliate_clean
    test_start_date = "2025-01-01"
    test_end_date = "2025-12-31"
    result = reconciliate_clean(test_start_date, test_end_date)

    with Session(engine_clean) as session:
        expected_revenue = session.execute(
            text(
                "SELECT SUM(commissie_cent) FROM clean_verkopen "
                "WHERE telt_mee_voor_omzet = 1 "
                "AND date(aangemaakt_op_nl) BETWEEN :start_date AND :end_date"
            ),
            {"start_date": test_start_date, "end_date": test_end_date},
        ).scalar() or 0

    assert f"Correct revenue: {expected_revenue}" in result
    assert "Use processing date instead of purchase date" in result
    assert "Include test partners" in result
    assert "Include unpaid, cancelled, or refunded sales" in result
    assert "Use customer price instead of commission" in result
    assert "Multiply commission by voucher quantity" in result
    assert "Use the raw purchase timestamp instead of Amsterdam time" in result
    assert "Treat the end date as exclusive" in result

