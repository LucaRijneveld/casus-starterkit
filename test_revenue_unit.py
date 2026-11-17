import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

import cleandatabase
import revenue
import sqldatabase


@pytest.fixture
def revenue_databases(monkeypatch):
    source_engine = create_engine("sqlite://")
    clean_engine = create_engine("sqlite://")
    sqldatabase.Base.metadata.create_all(source_engine)
    cleandatabase.Base.metadata.create_all(clean_engine)

    with Session(clean_engine) as session:
        session.add_all([
            cleandatabase.Stad(
                id=1, naam="Utrecht", land="NL", regio="Midden-Nederland"
            ),
            cleandatabase.Stad(
                id=2, naam="Amsterdam", land="NL", regio="Noord-Holland"
            ),
            cleandatabase.Stad(
                id=3, naam="Bergen", land="NL", regio="Noord-Holland"
            ),
            cleandatabase.Stad(
                id=4, naam="Bergen", land="BE", regio="Henegouwen"
            ),
            cleandatabase.Partner(
                id=10, naam="Twin Partner", stad_id=1, is_test=0
            ),
            cleandatabase.Partner(
                id=11, naam="Twin Partner", stad_id=1, is_test=0
            ),
            cleandatabase.Partner(
                id=12, naam="Twin Partner", stad_id=2, is_test=0
            ),
            cleandatabase.Partner(
                id=13, naam="Solo Partner", stad_id=2, is_test=0
            ),
            cleandatabase.Partner(
                id=20, naam="Test Partner", stad_id=1, is_test=1
            ),
            cleandatabase.Partner(
                id=14, naam="Bergen NL Partner", stad_id=3, is_test=0
            ),
            cleandatabase.Partner(
                id=15, naam="Bergen BE Partner", stad_id=4, is_test=0
            ),
        ])
        for deal_id, partner_id, partner_is_test in (
            (100, 10, 0), (101, 11, 0), (102, 12, 0),
            (103, 13, 0), (104, 20, 1), (105, 14, 0), (106, 15, 0),
        ):
            session.add(cleandatabase.Deal(
                id=deal_id,
                partner_id=partner_id,
                titel=f"Deal {deal_id}",
                start_datum="2025-01-01",
                eind_datum="2025-12-31",
                prijs_cent=10000,
                commissie_pct=20.0,
                partner_is_test=partner_is_test,
            ))

        sale_values = [
            (1, 100, "2025-01-01 00:00:00", "2025-02-01 10:00:00",
             "betaald", 2, 100000, 23020, 0, 1,
             "2025-01-01 01:00:00", "2025-02-01 11:00:00"),
            (2, 101, "2025-01-31 23:00:00", "2025-01-31 23:30:00",
             "betaald", 1, 40000, 12000, 0, 1,
             "2025-01-31 23:00:00", "2025-01-31 23:30:00"),
            (3, 102, "2025-01-10 10:00:00", "2025-01-10 11:00:00",
             "betaald", 1, 25000, 4000, 0, 1,
             "2025-01-10 11:00:00", "2025-01-10 12:00:00"),
            (4, 103, "2025-02-01 10:00:00", "2025-01-30 10:00:00",
             "betaald", 1, 25000, 5000, 0, 1,
             "2025-02-01 11:00:00", "2025-01-30 11:00:00"),
            (5, 104, "2025-01-15 10:00:00", "2025-01-15 11:00:00",
             "betaald", 1, 40000, 9000, 1, 0,
             "2025-01-15 11:00:00", "2025-01-15 12:00:00"),
            (6, 100, "2025-01-15 10:00:00", "2025-01-15 11:00:00",
             "geannuleerd", 1, 10000, 7000, 0, 0,
             "2025-01-15 11:00:00", "2025-01-15 12:00:00"),
            (7, 100, "2025-01-20 10:00:00", "2025-01-20 11:00:00",
             "terugbetaald", 1, 10000, 3000, 0, 0,
             "2025-01-20 11:00:00", "2025-01-20 12:00:00"),
            (8, 100, "2024-12-31 23:30:00", "2025-01-01 00:00:00",
             "betaald", 2, 5000, 1000, 0, 1,
             "2025-01-01 00:30:00", "2025-01-01 01:00:00"),
            (9, 105, "2025-03-10 10:00:00", "2025-03-10 11:00:00",
             "betaald", 1, 10000, 600, 0, 1,
             "2025-03-10 11:00:00", "2025-03-10 12:00:00"),
            (10, 106, "2025-03-10 10:00:00", "2025-03-10 11:00:00",
             "betaald", 1, 10000, 700, 0, 1,
             "2025-03-10 11:00:00", "2025-03-10 12:00:00"),
        ]
        session.add_all([
            cleandatabase.Verkoop(
                id=sale_id,
                deal_id=deal_id,
                aangemaakt_op=raw_purchase,
                verwerkt_op=raw_processing,
                status=status,
                aantal=quantity,
                klantprijs_cent=customer_price,
                commissie_cent=commission,
                klant_id=f"synthetic-{sale_id}",
                status_clean=status,
                partner_is_test=partner_is_test,
                telt_mee_voor_omzet=counts_for_revenue,
                aangemaakt_op_nl=local_purchase,
                verwerkt_op_nl=local_processing,
            )
            for (
                sale_id, deal_id, raw_purchase, raw_processing, status,
                quantity, customer_price, commission, partner_is_test,
                counts_for_revenue, local_purchase, local_processing,
            ) in sale_values
        ])
        session.commit()

    with Session(source_engine) as session:
        session.add_all([
            sqldatabase.Stad(
                id=1, naam="Utrecht", land="NL", regio="Midden-Nederland"
            ),
            sqldatabase.Partner(
                id=1, naam="Source Partner", stad_id=1, is_test=0
            ),
            sqldatabase.Partner(
                id=2, naam="Source Test Partner", stad_id=1, is_test=1
            ),
            sqldatabase.Deal(
                id=1, partner_id=1, titel="Source Deal",
                start_datum="2025-01-01", eind_datum="2025-12-31",
                prijs_cent=10000, commissie_pct=20.0,
            ),
            sqldatabase.Deal(
                id=2, partner_id=2, titel="Source Test Deal",
                start_datum="2025-01-01", eind_datum="2025-12-31",
                prijs_cent=10000, commissie_pct=20.0,
            ),
            sqldatabase.Verkoop(
                id=1, deal_id=1, aangemaakt_op="2025-01-15",
                verwerkt_op="2025-02-01", status="Betaald",
                aantal=1, klantprijs_cent=1000, commissie_cent=100,
                klant_email="private@example.invalid",
                betaalreferentie="PAYMENT-SECRET",
            ),
            sqldatabase.Verkoop(
                id=2, deal_id=2, aangemaakt_op="2025-01-16",
                verwerkt_op="2025-01-20", status="Betaald",
                aantal=1, klantprijs_cent=400, commissie_cent=40,
                klant_email="test@example.invalid",
                betaalreferentie="TEST-PAYMENT-SECRET",
            ),
        ])
        session.commit()

    monkeypatch.setattr(revenue, "engine_src", source_engine)
    monkeypatch.setattr(revenue, "engine_clean", clean_engine)
    yield
    source_engine.dispose()
    clean_engine.dispose()


def test_context_and_eda_are_safe_and_descriptive(revenue_databases):
    context = revenue.data_context()
    eda = revenue.exploratory_data_analysis()

    assert "telt_mee_voor_omzet" in context
    assert "Duplicate partner names" in context
    assert "Found 4 tables" in eda
    assert "PAYMENT-SECRET" not in eda
    assert "private@example.invalid" not in eda
    assert "Sensitive columns omitted: klant_email, betaalreferentie" in eda


def test_sql_tools_return_rows_from_their_configured_database(revenue_databases):
    assert revenue.src_sql("SELECT COUNT(*) FROM verkopen") == [(2,)]
    assert revenue.clean_sql("SELECT COUNT(*) FROM clean_verkopen") == [(10,)]


def test_sql_tools_surface_invalid_sql(revenue_databases):
    with pytest.raises(RuntimeError, match="An error occurred"):
        revenue.src_sql("SELECT missing_column FROM verkopen")
    with pytest.raises(RuntimeError, match="An error occurred"):
        revenue.clean_sql("SELECT missing_column FROM clean_verkopen")


def test_revenue_by_city_uses_eligible_sales_and_inclusive_local_dates(
    revenue_databases,
):
    result = revenue.omzet_per_stad("2025-01-01", "2025-01-31")

    assert "1\tUtrecht\tNL\tMidden-Nederland\t36020" in result
    assert "2\tAmsterdam\tNL\tNoord-Holland\t4000" in result
    assert "49020" not in result


def test_revenue_by_city_keeps_duplicate_names_separate_by_id(
    revenue_databases,
):
    result = revenue.omzet_per_stad("2025-03-01", "2025-03-31")

    assert "3\tBergen\tNL\tNoord-Holland\t600" in result
    assert "4\tBergen\tBE\tHenegouwen\t700" in result
    assert "Bergen\t1300" not in result


def test_revenue_by_partner_reports_both_id_and_name_city_views(
    revenue_databases,
):
    result = revenue.omzet_per_partner("2025-01-01", "2025-01-31")

    assert "10\tTwin Partner\tUtrecht\t24020" in result
    assert "11\tTwin Partner\tUtrecht\t12000" in result
    assert "12\tTwin Partner\tAmsterdam\t4000" in result
    assert "Twin Partner\tUtrecht\t36020" in result
    assert "Twin Partner\tAmsterdam\t4000" in result


def test_revenue_by_partner_limits_and_sorts_each_view(revenue_databases):
    result = revenue.omzet_per_partner("2025-01-01", "2025-01-31", n=1)

    assert "Separate partners (by ID) (top 1)" in result
    assert "10\tTwin Partner\tUtrecht\t24020" in result
    assert "11\tTwin Partner\tUtrecht\t12000" not in result
    assert "Combined by exact partner name and city (top 1)" in result
    assert "Twin Partner\tUtrecht\t36020" in result
    assert "Twin Partner\tAmsterdam\t4000" not in result
    assert revenue.omzet_per_partner(
        "2025-01-01", "2025-01-31", n=0
    ) == "The number of partners (n) must be at least 1."


def test_partner_search_returns_fields_and_handles_no_match(revenue_databases):
    city_result = revenue.zoek_stad("Utre")
    partner_result = revenue.zoek_partner("Twin")

    assert "ID\tNaam\tLand\tRegio" in city_result
    assert "1\tUtrecht\tNL\tMidden-Nederland" in city_result
    assert "10\tTwin Partner\tUtrecht\tNL" in partner_result
    assert "12\tTwin Partner\tAmsterdam\tNL" in partner_result
    assert "No cities found" in revenue.zoek_stad("not-a-city")
    assert "No partners found" in revenue.zoek_partner("not-a-partner")


def test_available_period_uses_clean_local_purchase_timestamps(revenue_databases):
    result = revenue.beschikbare_periode()

    assert "2025-01-01 00:30:00" in result
    assert "2025-03-10 11:00:00" in result


def test_monthly_revenue_groups_within_inclusive_date_range(revenue_databases):
    result = revenue.omzet_per_maand("2025-01-01", "2025-02-28")

    assert "2025-01\t40020" in result
    assert "2025-02\t5000" in result
    assert "2024-12" not in result


def test_period_comparison_calculates_each_range_independently(
    revenue_databases,
):
    result = revenue.vergelijk_periode(
        "2025-01-01", "2025-01-31", "2025-02-01", "2025-02-28"
    )

    assert "Periode 1 (2025-01-01 to 2025-01-31): 40020 cent" in result
    assert "Periode 2 (2025-02-01 to 2025-02-28): 5000 cent" in result


def test_top_partners_limits_each_grouping_view(revenue_databases):
    result = revenue.top_partners("2025-01-01", "2025-01-31", n=1)

    assert "Separate partners (by ID) (top 1)" in result
    assert "10\tTwin Partner\tUtrecht\t24020" in result
    assert "Combined by exact partner name and city (top 1)" in result
    assert "Twin Partner\tUtrecht\t36020" in result
    assert "Amsterdam\t4000" not in result


def test_reconciliation_clean_reports_baseline_and_rule_variances(
    revenue_databases,
):
    result = revenue.reconciliate_clean("2025-01-01", "2025-01-31")

    expected_lines = [
        "Correct revenue: 40020",
        "Use processing date instead of purchase date: 22000 (difference: -18020 cents)",
        "Include test partners: 49020 (difference: +9000 cents)",
        "Include unpaid, cancelled, or refunded sales: 50020 (difference: +10000 cents)",
        "Use customer price instead of commission: 170000 (difference: +129980 cents)",
        "Multiply commission by voucher quantity: 64040 (difference: +24020 cents)",
        "Use the raw purchase timestamp instead of Amsterdam time: 39020 (difference: -1000 cents)",
        "Treat the end date as exclusive: 28020 (difference: -12000 cents)",
    ]
    for line in expected_lines:
        assert line in result


def test_reconciliation_report_matches_amount_and_voucher_count(
    revenue_databases,
):
    with Session(revenue.engine_clean) as session:
        session.add_all([
            cleandatabase.Verkoop(
                id=100, deal_id=104,
                aangemaakt_op="2026-07-31 22:00:00",
                verwerkt_op="2026-07-31 22:30:00",
                status="betaald", aantal=5086,
                klantprijs_cent=5000000, commissie_cent=3461553,
                klant_id="synthetic-finance-example", status_clean="betaald",
                partner_is_test=1, telt_mee_voor_omzet=0,
                aangemaakt_op_nl="2026-08-01 00:00:00",
                verwerkt_op_nl="2026-08-01 00:30:00",
            ),
            cleandatabase.Verkoop(
                id=101, deal_id=100,
                aangemaakt_op="2026-07-31 22:00:00",
                verwerkt_op="2026-07-31 22:30:00",
                status="geannuleerd", aantal=1,
                klantprijs_cent=100, commissie_cent=100,
                klant_id="synthetic-cancelled", status_clean="geannuleerd",
                partner_is_test=0, telt_mee_voor_omzet=0,
                aangemaakt_op_nl="2026-08-01 00:00:00",
                verwerkt_op_nl="2026-08-01 00:30:00",
            ),
        ])
        session.commit()

    result = revenue.reconciliate_rapport(
        "2026-08-01", "2026-08-31", 3461553, vouchers=5086
    )

    assert "Exacte verklaring(en)" in result
    assert "3461553 cent, 5086 vouchers" in result
    assert "testpartners meegeteld" in result
    assert "verwerkingsdatum" in result
    assert "alle statussen" not in result


def test_reconciliation_report_returns_all_128_matches(revenue_databases):
    result = revenue.reconciliate_rapport(
        "2030-01-01", "2030-01-31", 0
    )

    assert result.startswith("Exacte verklaring(en)")
    assert len(result.splitlines()) == 129


def test_reconciliation_report_returns_three_nearest_with_differences(
    revenue_databases,
):
    result = revenue.reconciliate_rapport(
        "2025-01-01", "2025-01-31", 999999999, vouchers=99
    )

    lines = result.splitlines()
    assert lines[0] == "Geen exacte combinatie. Dichtstbijzijnde varianten:"
    assert len(lines) == 4
    assert "bedragverschil:" in lines[1]
    assert "voucher-verschil:" in lines[1]


@pytest.mark.parametrize(
    ("start_date", "end_date", "amount", "vouchers", "message"),
    [
        ("2025-1-01", "2025-01-31", 1, None, "YYYY-MM-DD"),
        ("2025-02-01", "2025-01-31", 1, None, "on or after"),
        ("2025-01-01", "2025-01-31", 1.5, None, "integer number of cents"),
        ("2025-01-01", "2025-01-31", 1, -1, "non-negative integer"),
    ],
)
def test_reconciliation_report_validates_inputs(
    revenue_databases, start_date, end_date, amount, vouchers, message
):
    result = revenue.reconciliate_rapport(
        start_date, end_date, amount, vouchers
    )
    assert message in result


def test_reporting_tools_return_clear_empty_period_results(revenue_databases):
    assert "geen inkomsten gevonden" in revenue.omzet_per_stad(
        "2026-01-01", "2026-01-31"
    )
    assert "geen inkomsten gevonden" in revenue.omzet_per_partner(
        "2026-01-01", "2026-01-31"
    )
    assert "geen inkomsten gevonden" in revenue.omzet_per_maand(
        "2026-01-01", "2026-01-31"
    )
    assert "geen inkomsten gevonden" in revenue.top_partners(
        "2026-01-01", "2026-01-31"
    )
