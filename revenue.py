from datetime import date
from itertools import product
from pathlib import Path
from sqlalchemy import select, func, MetaData, Integer, Float, text
from sqlalchemy.orm import Session  
from mcp.server.fastmcp import FastMCP
import sqldatabase
import cleandatabase


class mcp(FastMCP):
    """Concrete FastMCP subclass with a useful fallback implementation for abstract hooks."""

    def __init__(self, name: str):
        super().__init__(name)

    def _get_server_info(self):
        return {
            "name": self.name,
            "type": "FastMCP",
            "description": "Social Deal Revenue Calculator (SQLAlchemy ORM)",
        }

    def _get_tools(self):
        tools = {}
        for attr_name in dir(self):
            value = getattr(self, attr_name)
            if callable(value) and getattr(value, "_is_tool", False):
                tools[attr_name] = value
        return tools


mcp = mcp("Social Deal Revenue Calculator (SQLAlchemy ORM)")
CONTEXT_FILE = Path(__file__).parent / "business_context.md"
DB_PATH = sqldatabase.DB_PATH  # Use the DB_PATH from sqldatabase.py (socialdeal_casus.sqlite)
engine_src = sqldatabase.engine  # Use the engine from sqldatabase.py (socialdeal_casus.sqlite)
engine_clean = cleandatabase.engine
SENSITIVE_SOURCE_COLUMNS = {"klant_email", "betaalreferentie"}


def _clean_date_range(column, start_date: str, end_date: str):
    return func.date(column).between(start_date, end_date)


def _partner_revenue_query(start_date: str, end_date: str, separate_by_id: bool):
    partner = cleandatabase.Partner
    city = cleandatabase.Stad
    sale = cleandatabase.Verkoop
    columns = []
    group_columns = [partner.naam, city.naam]
    if separate_by_id:
        columns.append(partner.id.label("Partner ID"))
        group_columns.insert(0, partner.id)
    columns.extend([
        partner.naam.label("Partner"),
        city.naam.label("Stad"),
        func.sum(sale.commissie_cent).label("Totale Omzet (cent)"),
    ])
    query = (
        select(*columns)
        .join(cleandatabase.Deal, partner.id == cleandatabase.Deal.partner_id)
        .join(sale, cleandatabase.Deal.id == sale.deal_id)
        .join(city, partner.stad_id == city.id)
        .where(_clean_date_range(sale.aangemaakt_op_nl, start_date, end_date))
        .where(sale.telt_mee_voor_omzet == 1)
        .group_by(*group_columns)
    )
    tie_breakers = [partner.id] if separate_by_id else [partner.naam, city.naam]
    return query.order_by(
        func.sum(sale.commissie_cent).desc(),
        *tie_breakers,
    )


@mcp.tool()
def data_context() -> str:
    """This tool provides a data context summary
    it explains what the data means, what is available in the database, and how we
    interpret the data. It also provides a summary of the data available in the database,
    including the number of deals, partners, and sales, as well as the date range of the data.
    In addition it will provide you some instructions on how to use the data safely and responsibly.
    
    Call this FIRST before running any other tools, as it will help you get an understanding of the
    data and the business context.
    
    Do not write any SQL before calling this tool.
    """
    try:
        return CONTEXT_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "Context file not found. Please ensure 'business_context.md' is present in the same directory as this script."
    
@mcp.tool()
def exploratory_data_analysis() -> str:
    """This tool provides an exploratory data analysis of the database.
    It will provide a summary of the tables, their structure, and some sample data.
    It will also provide some basic statistics about the data, such as the number of rows in each table,
    and the number of unique values in each column.
    
    Call this tool after calling the data_context tool, as it will help you get an understanding of the
    data and the business context.
    
    Do not write any SQL before calling this tool.
    """
    try:
        with Session(engine_src) as session:
            metadata = MetaData()
            metadata.reflect(bind=engine_src)
            tables = metadata.tables.keys()
            analysis_summary = f"Found {len(tables)} tables: {list(tables)}\n\n"
            
            # Give an overview of the tables
            for table_name in tables:
                table = metadata.tables[table_name]
                row_count = session.execute(select(func.count()).select_from(table)).scalar()
                analysis_summary += f"TABLE: {table_name}\n"
                analysis_summary += f"Total Rows: {row_count:,}\n"
                analysis_summary += "Columns:\n"
                for column in table.columns:
                    analysis_summary += f" - {column.name} ({column.type})\n"
                analysis_summary += "\n"
            
            # Sample data from each table
            for table_name in tables:
                table = metadata.tables[table_name]
                sample_columns = [
                    column for column in table.columns
                    if column.name not in SENSITIVE_SOURCE_COLUMNS
                ]
                omitted_columns = [
                    column.name for column in table.columns
                    if column.name in SENSITIVE_SOURCE_COLUMNS
                ]
                analysis_summary += f"Sample Data from {table_name}:\n"
                if omitted_columns:
                    analysis_summary += (
                        f"Sensitive columns omitted: {', '.join(omitted_columns)}\n"
                    )
                for row in session.execute(select(*sample_columns).limit(3)):
                    analysis_summary += f"{row}\n"
                analysis_summary += "\n"
            
            # Basic statistics for each table
            for table_name in tables:
                table = metadata.tables[table_name]
                analysis_summary += f"Basic Statistics for {table_name}:\n"
                for column in table.columns:
                    if isinstance(column.type, (Integer, Float)):
                        unique_count = session.execute(select(func.count(func.distinct(column))).select_from(table)).scalar()
                        analysis_summary += f" - {column.name}: {unique_count} unique values\n"
                analysis_summary += "\n"
            
            # Data quality checks
            for table_name in tables:
                table = metadata.tables[table_name]
                analysis_summary += f"Data Quality Checks for {table_name}:\n"
                for column in table.columns:
                    null_count = session.execute(select(func.count()).select_from(table).where(column.is_(None))).scalar()
                    analysis_summary += f" - {column.name}: {null_count} NULL values\n"
                analysis_summary += "\n"
                
            return analysis_summary
    except Exception as e:
        return f"An error occurred during EDA: {e}"

@mcp.tool()
def src_sql(query: str):
    """This tool allows you to run read-only SQL queries against the sourcedatabase.
    It returns raw rows as a Python list of tuples so that downstream code can process the result
    reliably. The helper is intentionally simple and safe for read-only analysis.
    """
    try:
        with Session(engine_src) as session:
            result = session.execute(text(query))
            return result.fetchall()
    except Exception as e:
        raise RuntimeError(f"An error occurred while executing the query: {e}") from e


@mcp.tool()
def clean_sql(query: str):
    """This tool allows you to run read-only SQL queries against the clean database.
    It returns raw rows as a Python list of tuples so that downstream code can process the result
    reliably. The helper is intentionally simple and safe for read-only analysis.
    """
    try:
        with Session(engine_clean) as session:
            result = session.execute(text(query))
            return result.fetchall()
    except Exception as e:
        raise RuntimeError(f"An error occurred while executing the query: {e}") from e


# Compatibility aliases used by tests and scripts that expect a SQL-query tool.
sql_query_tool = clean_sql
src_sql_tool = src_sql
clean_sql_tool = clean_sql
    
@mcp.tool()
def omzet_per_stad(start_date: str, end_date: str) -> str:
    """Calculate revenue per city ID, showing location details for duplicate names."""
    try:
        with Session(engine_clean) as session:
            city = cleandatabase.Stad
            query = select(
                city.id.label("Stad ID"),
                city.naam.label("Stad"),
                city.land.label("Land"),
                city.regio.label("Regio"),
                func.sum(cleandatabase.Verkoop.commissie_cent).label("Totale Omzet (cent)")
            ).join(cleandatabase.Partner, city.id == cleandatabase.Partner.stad_id
            ).join(cleandatabase.Deal, cleandatabase.Partner.id == cleandatabase.Deal.partner_id
            ).join(cleandatabase.Verkoop, cleandatabase.Deal.id == cleandatabase.Verkoop.deal_id
            ).where(_clean_date_range(cleandatabase.Verkoop.aangemaakt_op_nl, start_date, end_date)
            ).where(cleandatabase.Verkoop.telt_mee_voor_omzet == 1
            ).group_by(city.id, city.naam, city.land, city.regio
            ).order_by(
                func.sum(cleandatabase.Verkoop.commissie_cent).desc(),
                city.id,
            )

            result = session.execute(query)
            rows = result.fetchall()

            if not rows:
                return "Omzet per stad: geen inkomsten gevonden."

            formatted_result = "Omzet per stad\n"
            formatted_result += "\t".join(result.keys()) + "\n"
            formatted_result += "-" * 50 + "\n"
            for row in rows:
                formatted_result += "\t".join(str(value) for value in row) + "\n"
            return formatted_result
    except Exception as e:
        return f"An error occurred while calculating revenue per city: {e}"

@mcp.tool()
def omzet_per_partner(start_date: str, end_date: str, n: int = 5) -> str:
    """Report the top N partner revenue totals by ID and by exact name and city."""
    try:
        if n < 1:
            return "The number of partners (n) must be at least 1."

        with Session(engine_clean) as session:
            reports = []
            for title, separate_by_id in (
                ("Separate partners (by ID)", True),
                ("Combined by exact partner name and city", False),
            ):
                result = session.execute(
                    _partner_revenue_query(start_date, end_date, separate_by_id)
                    .limit(n)
                )
                rows = result.fetchall()
                if rows:
                    section = [f"{title} (top {n})", "\t".join(result.keys()), "-" * 50]
                    section.extend(
                        "\t".join(str(value) for value in row) for row in rows
                    )
                    reports.append("\n".join(section))

            if not reports:
                return "Omzet per partner: geen inkomsten gevonden."
            return "Omzet per partner\n\n" + "\n\n".join(reports)
    except Exception as e:
        return f"An error occurred while calculating revenue per partner: {e}"

@mcp.tool()
def zoek_stad(naam: str) -> str:
    """This tool allows you to search for a city by name in the clean database.
    It will return the details of the city, including its ID, name, country, and region.
    
    Call this tool after calling the data_context and exploratory_data_analysis tools, as it will help you get an understanding of the
    data and the business context.
    
    Do not write any SQL before calling these tools.
    """
    try:
        with Session(engine_clean) as session:
            query = select(
                cleandatabase.Stad.id.label("ID"),
                cleandatabase.Stad.naam.label("Naam"),
                cleandatabase.Stad.land.label("Land"),
                cleandatabase.Stad.regio.label("Regio"),
            ).where(cleandatabase.Stad.naam.ilike(f"%{naam}%"))
            result = session.execute(query)
            rows = result.fetchall()
            
            if not rows:
                return f"No cities found matching '{naam}'."

            formatted_result = f"Cities matching '{naam}':\n"
            formatted_result += "\t".join(result.keys()) + "\n"
            formatted_result += "-" * 50 + "\n"
            for row in rows:
                formatted_result += "\t".join(str(value) for value in row) + "\n"
            return formatted_result
    except Exception as e:
        return f"An error occurred while searching for cities: {e}"

@mcp.tool()
def zoek_partner(naam: str) -> str:
    """This tool allows you to search for a partner by name in the clean database.
    It will return the details of the partner, including its ID, name, and associated city.
    
    Call this tool after calling the data_context and exploratory_data_analysis tools, as it will help you get an understanding of the
    data and the business context.
    
    Do not write any SQL before calling these tools.
    """
    try:
        with Session(engine_clean) as session:
            query = select(
                cleandatabase.Partner.id.label("ID"),
                cleandatabase.Partner.naam.label("Partner"),
                cleandatabase.Stad.naam.label("Stad"),
                cleandatabase.Stad.land.label("Land"),
            ).join(
                cleandatabase.Stad,
                cleandatabase.Partner.stad_id == cleandatabase.Stad.id,
            ).where(cleandatabase.Partner.naam.ilike(f"%{naam}%"))
            result = session.execute(query)
            rows = result.fetchall()
            
            if not rows:
                return f"No partners found matching '{naam}'."

            formatted_result = f"Partners matching '{naam}':\n"
            formatted_result += "\t".join(result.keys()) + "\n"
            formatted_result += "-" * 50 + "\n"
            for row in rows:
                formatted_result += "\t".join(str(value) for value in row) + "\n"
            return formatted_result
    except Exception as e:
        return f"An error occurred while searching for partners: {e}"

@mcp.tool()
def beschikbare_periode() -> str:
    """This tool provides the available date range of the sales data in the clean database."""
    try:
        with Session(engine_clean) as session:
            query = select(
                func.min(cleandatabase.Verkoop.aangemaakt_op_nl).label("Earliest Sale Date"),
                func.max(cleandatabase.Verkoop.aangemaakt_op_nl).label("Latest Sale Date")
            )
            result = session.execute(query)
            row = result.fetchone()

            if not row:
                return "Beschikbare periode: geen verkoopdata gevonden."

            return f"Beschikbare periode\nEarliest Sale Date: {row[0]}\nLatest Sale Date: {row[1]}"
    except Exception as e:
        return f"An error occurred while retrieving the available sales period: {e}"

@mcp.tool()
def omzet_per_maand(start_date: str, end_date: str) -> str:
    """This tool calculates the total revenue per month from the clean database."""
    try:
        with Session(engine_clean) as session:
            query = select(
                func.strftime("%Y-%m", cleandatabase.Verkoop.aangemaakt_op_nl).label("Month"),
                func.sum(cleandatabase.Verkoop.commissie_cent).label("Totale Omzet (cent)")
            ).where(_clean_date_range(cleandatabase.Verkoop.aangemaakt_op_nl, start_date, end_date)
            ).where(cleandatabase.Verkoop.telt_mee_voor_omzet == 1
            ).group_by(func.strftime("%Y-%m", cleandatabase.Verkoop.aangemaakt_op_nl))

            result = session.execute(query)
            rows = result.fetchall()

            if not rows:
                return "Omzet per maand: geen inkomsten gevonden."

            formatted_result = "Omzet per maand\n"
            formatted_result += "\t".join(result.keys()) + "\n"
            formatted_result += "-" * 50 + "\n"
            for row in rows:
                formatted_result += "\t".join(str(value) for value in row) + "\n"
            return formatted_result
    except Exception as e:
        return f"An error occurred while calculating revenue per month: {e}"

@mcp.tool()
def vergelijk_periode(start_date_1: str, end_date_1: str, start_date_2: str, end_date_2: str) -> str:
    """This tool compares the total revenue between two specified periods from the clean database."""
    try:
        with Session(engine_clean) as session:
            def total(period_start: str, period_end: str) -> int:
                query = select(
                    func.sum(cleandatabase.Verkoop.commissie_cent).label("Totale Omzet (cent)")
                ).where(_clean_date_range(cleandatabase.Verkoop.aangemaakt_op_nl, period_start, period_end)
                ).where(cleandatabase.Verkoop.telt_mee_voor_omzet == 1)
                return session.execute(query).scalar() or 0

            omzet_periode1 = total(start_date_1, end_date_1)
            omzet_periode2 = total(start_date_2, end_date_2)

            return (
                "Vergelijking van periodes\n"
                f"Periode 1 ({start_date_1} to {end_date_1}): {omzet_periode1} cent\n"
                f"Periode 2 ({start_date_2} to {end_date_2}): {omzet_periode2} cent"
            )
    except Exception as e:
        return f"An error occurred while comparing revenue between periods: {e}"

@mcp.tool()
def top_partners(start_date: str, end_date: str, n: int = 5) -> str:
    """Show the top N partners separately by ID and combined by exact name and city."""
    try:
        with Session(engine_clean) as session:
            reports = []
            for title, separate_by_id in (
                ("Separate partners (by ID)", True),
                ("Combined by exact partner name and city", False),
            ):
                query = (
                    _partner_revenue_query(start_date, end_date, separate_by_id)
                    .order_by(
                        func.sum(cleandatabase.Verkoop.commissie_cent).desc()
                    )
                    .limit(n)
                )
                result = session.execute(query)
                rows = result.fetchall()
                if rows:
                    section = [f"{title} (top {n})", "\t".join(result.keys()), "-" * 50]
                    section.extend(
                        "\t".join(str(value) for value in row) for row in rows
                    )
                    reports.append("\n".join(section))

            if not reports:
                return "Top partners: geen inkomsten gevonden."
            return "Top partners\n\n" + "\n\n".join(reports)
    except Exception as e:
        return f"An error occurred while retrieving top partners: {e}"
    
@mcp.tool()
def reconciliate_clean(start_datum: str, eind_datum: str) -> str:
    """Reconcile clean revenue against common reporting mistakes for an inclusive date period.

    The baseline is commission from paid, non-test sales, recognized on the Amsterdam-local
    purchase date. Each alternative changes one reporting rule so its variance is attributable.
    
    Call this tool after calling the data_context and exploratory_data_analysis tools, 
    as it will help you get an understanding of the data and the business context.
    """
    try:
        with Session(engine_clean) as session:
            sale = cleandatabase.Verkoop

            def total_for_period(amount_column, *filters):
                query = select(func.sum(amount_column)).where(*filters)
                return session.scalar(query) or 0

            purchase_period = _clean_date_range(
                sale.aangemaakt_op_nl, start_datum, eind_datum
            )
            eligible = sale.telt_mee_voor_omzet == 1
            correct_revenue = total_for_period(
                sale.commissie_cent, purchase_period, eligible
            )

            scenarios = [
                (
                    "Use processing date instead of purchase date",
                    total_for_period(
                        sale.commissie_cent,
                        _clean_date_range(
                            sale.verwerkt_op_nl, start_datum, eind_datum
                        ),
                        eligible,
                    ),
                ),
                (
                    "Include test partners",
                    total_for_period(
                        sale.commissie_cent,
                        purchase_period,
                        sale.status_clean == "betaald",
                    ),
                ),
                (
                    "Include unpaid, cancelled, or refunded sales",
                    total_for_period(
                        sale.commissie_cent,
                        purchase_period,
                        sale.partner_is_test == 0,
                    ),
                ),
                (
                    "Use customer price instead of commission",
                    total_for_period(
                        sale.klantprijs_cent, purchase_period, eligible
                    ),
                ),
                (
                    "Multiply commission by voucher quantity",
                    total_for_period(
                        sale.commissie_cent * sale.aantal,
                        purchase_period,
                        eligible,
                    ),
                ),
                (
                    "Use the raw purchase timestamp instead of Amsterdam time",
                    total_for_period(
                        sale.commissie_cent,
                        _clean_date_range(
                            sale.aangemaakt_op, start_datum, eind_datum
                        ),
                        eligible,
                    ),
                ),
                (
                    "Treat the end date as exclusive",
                    total_for_period(
                        sale.commissie_cent,
                        func.date(sale.aangemaakt_op_nl) >= start_datum,
                        func.date(sale.aangemaakt_op_nl) < eind_datum,
                        eligible,
                    ),
                ),
            ]

            lines = [
                "Clean Revenue Reconciliation (amounts in cents)",
                f"Period: {start_datum} through {eind_datum} (inclusive)",
                f"Correct revenue: {correct_revenue}",
                "One-rule-at-a-time reporting alternatives:",
            ]
            for label, scenario_revenue in scenarios:
                difference = scenario_revenue - correct_revenue
                lines.append(
                    f"- {label}: {scenario_revenue} "
                    f"(difference: {difference:+} cents)"
                )
            return "\n".join(lines)
    except Exception as e:
        return f"An error occurred while performing reconciliation check: {e}"


@mcp.tool()
def reconciliate_rapport(
    start_datum: str,
    eind_datum: str,
    bedrag_cent: int,
    vouchers: int | None = None,
) -> str:
    """Find reporting-rule combinations that explain a reported amount.

    Use this when another team reports a discrepant figure. For the authoritative
    revenue calculation and one-rule-at-a-time variances, use reconciliate_clean.

    Args:
        start_datum: Inclusive period start in YYYY-MM-DD format.
        eind_datum: Period end in YYYY-MM-DD format.
        bedrag_cent: Reported revenue in integer cents.
        vouchers: Optional reported voucher count to match alongside revenue.
    """
    try:
        if not isinstance(start_datum, str) or not isinstance(eind_datum, str):
            return "Dates must use YYYY-MM-DD format."
        try:
            start = date.fromisoformat(start_datum)
            end = date.fromisoformat(eind_datum)
        except ValueError:
            return "Dates must use YYYY-MM-DD format."
        if start.isoformat() != start_datum or end.isoformat() != eind_datum:
            return "Dates must use YYYY-MM-DD format."
        if end < start:
            return "The end date must be on or after the start date."
        if isinstance(bedrag_cent, bool) or not isinstance(bedrag_cent, int):
            return "The reported amount must be an integer number of cents."
        if vouchers is not None and (
            isinstance(vouchers, bool) or not isinstance(vouchers, int) or vouchers < 0
        ):
            return "The voucher count must be a non-negative integer."

        variants = []
        date_columns = {
            (False, False): "date(aangemaakt_op_nl)",
            (True, False): "date(verwerkt_op_nl)",
            (False, True): "substr(aangemaakt_op, 1, 10)",
            (True, True): "substr(verwerkt_op, 1, 10)",
        }

        with engine_clean.connect() as connection:
            for (
                processing_date,
                raw_timestamp,
                include_test_partners,
                include_all_statuses,
                exclusive_end,
                use_customer_price,
                multiply_by_quantity,
            ) in product((False, True), repeat=7):
                date_column = date_columns[(processing_date, raw_timestamp)]
                amount_column = (
                    "klantprijs_cent" if use_customer_price else "commissie_cent"
                )
                amount_expression = (
                    f"{amount_column} * aantal"
                    if multiply_by_quantity else amount_column
                )
                end_operator = "<" if exclusive_end else "<="
                filters = [
                    f"{date_column} >= :start_date",
                    f"{date_column} {end_operator} :end_date",
                ]
                if not include_test_partners:
                    filters.append("partner_is_test = 0")
                if not include_all_statuses:
                    filters.append("status_clean = 'betaald'")

                query = text(
                    "SELECT COALESCE(SUM("
                    f"{amount_expression}), 0), "
                    "COALESCE(SUM(aantal), 0) "
                    "FROM clean_verkopen WHERE "
                    + " AND ".join(filters)
                )
                amount, voucher_count = connection.execute(
                    query,
                    {"start_date": start_datum, "end_date": eind_datum},
                ).one()

                deviations = []
                if processing_date:
                    deviations.append("verwerkingsdatum")
                if raw_timestamp:
                    deviations.append("ruwe timestamp")
                if include_test_partners:
                    deviations.append("testpartners meegeteld")
                if include_all_statuses:
                    deviations.append("alle statussen")
                if exclusive_end:
                    deviations.append("einddatum exclusief")
                if use_customer_price:
                    deviations.append("klantprijs i.p.v. commissie")
                if multiply_by_quantity:
                    deviations.append("bedrag vermenigvuldigd met aantal")

                variants.append({
                    "amount": amount,
                    "vouchers": voucher_count,
                    "deviations": deviations,
                })

        def describe(variant: dict) -> str:
            rules = variant["deviations"] or [
                "basisregels (aankoopdatum NL, alleen betaald, geen testpartners)"
            ]
            return (
                f"{variant['amount']} cent, {variant['vouchers']} vouchers: "
                + ", ".join(rules)
            )

        exact_matches = [
            variant for variant in variants
            if variant["amount"] == bedrag_cent
            and (vouchers is None or variant["vouchers"] == vouchers)
        ]
        if exact_matches:
            exact_matches.sort(
                key=lambda variant: (
                    len(variant["deviations"]),
                    tuple(variant["deviations"]),
                )
            )
            lines = [
                f"Exacte verklaring(en) voor {bedrag_cent} cent"
                + (f" en {vouchers} vouchers" if vouchers is not None else "")
                + " (minst afwijkingen eerst):"
            ]
            lines.extend(f"- {describe(variant)}" for variant in exact_matches)
            return "\n".join(lines)

        closest = sorted(
            variants,
            key=lambda variant: (
                abs(variant["amount"] - bedrag_cent),
                abs(variant["vouchers"] - vouchers) if vouchers is not None else 0,
                len(variant["deviations"]),
                tuple(variant["deviations"]),
            ),
        )[:3]
        lines = ["Geen exacte combinatie. Dichtstbijzijnde varianten:"]
        for variant in closest:
            line = (
                f"- {describe(variant)} "
                f"(bedragverschil: {variant['amount'] - bedrag_cent:+d} cent"
            )
            if vouchers is not None:
                line += (
                    f", voucher-verschil: {variant['vouchers'] - vouchers:+d}"
                )
            lines.append(line + ")")
        return "\n".join(lines)
    except Exception as e:
        return f"An error occurred while searching reporting-rule combinations: {e}"
    

if __name__ == "__main__":
    mcp.run()


